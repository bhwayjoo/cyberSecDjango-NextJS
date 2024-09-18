import socket
import requests
from bs4 import BeautifulSoup
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import sublist3r
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
import warnings
from Wappalyzer import Wappalyzer, WebPage
import google.generativeai as genai
from django.conf import settings
import logging
from .models import Domain, Subdomain, OpenPort, CrawledPage, Technology
from .serializers import DomainSerializer, SubdomainSerializer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ignore warnings
warnings.filterwarnings("ignore")

# Configure Gemini API
genai.configure(api_key=settings.GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

class SubdomainSearch(APIView):
    def post(self, request):
        domain = request.data.get('domain')

        if not domain:
            return Response({"error": "Domain name is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate the domain
        validate = URLValidator()
        try:
            validate(f'http://{domain}')
        except ValidationError:
            return Response({"error": "Invalid domain"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Delete the existing domain if it exists
            Domain.objects.filter(name=domain).delete()

            # Create a new domain object and set initial status
            domain_obj = Domain.objects.create(name=domain, status="in_progress")

            # Check Gemini API status
            if not self.check_gemini_api_status():
                logger.warning("Gemini API is not responding. Proceeding without advanced analysis.")

            # Retrieve subdomains using sublist3r
            subdomains = sublist3r.main(domain, 40, savefile=None, ports=None, silent=True, verbose=False, enable_bruteforce=False, engines=None)
            if not subdomains:
                domain_obj.status = "complete"
                domain_obj.save()
                return Response({"message": "No subdomains found", "domain_id": domain_obj.id, "status": "complete"}, status=status.HTTP_200_OK)

            subdomain_results = []

            # Use ThreadPoolExecutor to scan subdomains in parallel
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_subdomain = {executor.submit(self.scan_subdomain, subdomain): subdomain for subdomain in subdomains}
                for future in as_completed(future_to_subdomain):
                    result = future.result()
                    # Only append subdomains that resolved to an IP
                    if result.get('ip'):
                        subdomain_results.append(result)

            # Crawl the root domain and analyze technologies
            root_crawled_pages = self.crawl_website(f'http://{domain}', f'http://{domain}', set())
            root_technologies = self.identify_technologies(f'http://{domain}')
            root_result = {
                "subdomain": domain,
                "status": "reachable",
                "crawled_pages": root_crawled_pages,
                "technologies": root_technologies,
                "gemini_analysis": self.analyze_with_gemini({
                    'open_ports': [],  # No specific open ports for root domain
                    'technologies': root_technologies
                })
            }
            subdomain_results.append(root_result)

            # Save results to database
            for result in subdomain_results:
                subdomain_obj = Subdomain.objects.create(
                    domain=domain_obj,
                    name=result['subdomain'],
                    ip=result.get('ip'),
                    status=result['status'],
                    gemini_analysis=result.get('gemini_analysis')
                )
                
                for port_data in result.get('open_ports', []):
                    OpenPort.objects.create(
                        subdomain=subdomain_obj,
                        port=port_data['port'],
                        status=port_data['status'],
                        service=port_data['service'],
                        version=port_data['version']
                    )
                
                for page_data in result.get('crawled_pages', []):
                    CrawledPage.objects.create(
                        subdomain=subdomain_obj,
                        url=page_data['url'],
                        title=page_data['title'],
                        status_code=page_data['status_code']
                    )
                
                for tech in result.get('technologies', []):
                    Technology.objects.create(
                        subdomain=subdomain_obj,
                        name=tech
                    )

            # Set status to complete
            domain_obj.status = "complete"
            domain_obj.save()

            # Serialize the data
            serializer = DomainSerializer(domain_obj)
            
            # Create the response data
            response_data = {
                "domain_id": domain_obj.id,
                "domain_data": serializer.data,
                "status": domain_obj.status
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            if 'domain_obj' in locals():
                domain_obj.status = "error"
                domain_obj.save()
            return Response({"error": "An unexpected error occurred", "domain_id": domain_obj.id, "status": "error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def check_gemini_api_status(self):
        try:
            model.generate_content("Test")
            return True
        except Exception as e:
            logger.error(f"Gemini API check failed: {str(e)}")
            return False

    def grab_banner(self, ip, port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                sock.connect((ip, port))

                if port in [80, 443, 8080, 8443]:
                    sock.sendall(b'HEAD / HTTP/1.0\r\nHost: ' + ip.encode() + b'\r\n\r\n')
                elif port == 21:
                    sock.sendall(b'HELP\r\n')  # FTP
                elif port == 25:
                    sock.sendall(b'EHLO example.com\r\n')  # SMTP
                sock.settimeout(1)
                banner = sock.recv(1024).decode('utf-8', errors='ignore')
                return banner.strip()
        except Exception as e:
            logger.error(f"Error grabbing banner for {ip}:{port}: {str(e)}")
            return None

    def get_service_info(self, port, banner):
        if not banner:
            return "unknown", "unknown"
        if port in [80, 443, 8080, 8443]:
            if "Server:" in banner:
                server = banner.split("Server:")[1].split("\r\n")[0].strip()
                return "HTTP", server
            return "HTTP", "unknown"
        if port == 22 and "SSH" in banner:
            return "SSH", banner.split()[0]
        if port == 21 and "FTP" in banner:
            return "FTP", banner.split()[0]
        if port == 25 and "SMTP" in banner:
            return "SMTP", banner.split()[0]
        if port == 3306 and "mysql" in banner.lower():
            return "MySQL", banner.split()[0]
        return "unknown", banner.split()[0] if banner else "unknown"

    def identify_technologies(self, url):
        wappalyzer = Wappalyzer.latest()
        try:
            webpage = WebPage.new_from_url(url)
            technologies = wappalyzer.analyze(webpage)
            return technologies
        except Exception as e:
            logger.error(f"Error identifying technologies for {url}: {str(e)}")
            return f"An error occurred: {e}"

    def analyze_with_gemini(self, subdomain_data):
        prompt = f"""
        Analyze the following subdomain information and provide insights:
        Open Ports: {subdomain_data.get('open_ports', 'N/A')}

        Please provide a summary of potential security implications based on the open ports and services and technologies {subdomain_data.get('technologies', 'N/A')}.
        """
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            return "Unable to perform advanced analysis due to API error."

    def scan_subdomain(self, subdomain):
        try:
            # Attempt to resolve the subdomain to an IP
            ip = socket.gethostbyname(subdomain)

            open_ports = []
            crawled_pages = []
            identified_technologies = []

            ports_to_scan = [80, 443, 21, 22, 25, 3306, 8080, 8443]

            for port in ports_to_scan:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(1)
                        result = sock.connect_ex((ip, port))
                        if result == 0:
                            banner = self.grab_banner(ip, port)
                            service, version = self.get_service_info(port, banner)
                            open_ports.append({
                                "port": port,
                                "status": "open",
                                "service": service,
                                "version": version
                            })

                            # If the port is HTTP or HTTPS, crawl the subdomain
                            if port in [80, 443]:
                                protocol = 'https' if port == 443 else 'http'
                                subdomain_url = f'{protocol}://{subdomain}'
                                crawled_pages.extend(self.crawl_website(subdomain_url, subdomain_url, set()))
                                technologies = self.identify_technologies(subdomain_url)
                                identified_technologies.append(technologies)

                except socket.error as e:
                    logger.error(f"Socket error for {subdomain}:{port} - {e}")

            # If no ports are open, return early and skip crawling/analysis
            if not open_ports:
                return {
                    "subdomain": subdomain,
                    "ip": ip,
                    "status": "no open ports",
                    "crawled_pages": [],
                    "technologies": [],
                    "gemini_analysis": "No open ports, skipping further analysis."
                }

            subdomain_data = {
                "subdomain": subdomain,
                "ip": ip,
                "status": "reachable",
                "open_ports": open_ports,
                "crawled_pages": crawled_pages,
                "technologies": identified_technologies
            }

            subdomain_data["gemini_analysis"] = self.analyze_with_gemini(subdomain_data)

            return subdomain_data
        except socket.gaierror:
            # If the subdomain doesn't resolve, return the subdomain without IP
            logger.warning(f"Subdomain {subdomain} could not resolve to an IP address")
            return {
                "subdomain": subdomain,
                "status": "unreachable",
                "ip": None,
                "crawled_pages": [],
                "technologies": [],
                "gemini_analysis": "Subdomain could not resolve, no analysis performed."
            }
        except Exception as e:
            logger.error(f"Error scanning subdomain {subdomain}: {str(e)}")
            return {
                "subdomain": subdomain,
                "status": "error",
                "ip": None,
                "crawled_pages": [],
                "technologies": [],
                "gemini_analysis": "An error occurred during the scan."
            }

    def crawl_website(self, url, base_url, crawled_urls):
        crawled_pages = []
        try:
            response = requests.get(url, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Add the page to the crawled list
            crawled_pages.append({
                "url": url,
                "title": soup.title.string if soup.title else "No title",
                "status_code": response.status_code
            })

            # Extract links
            links = [urljoin(base_url, link.get('href')) for link in soup.find_all('a', href=True)]
            for link in links:
                if link not in crawled_urls and link.startswith(base_url):
                    crawled_urls.add(link)
                    crawled_pages.extend(self.crawl_website(link, base_url, crawled_urls))
        except requests.RequestException as e:
            logger.error(f"Error crawling {url}: {str(e)}")
        return crawled_pages

class DomainDetail(APIView):
    def get(self, request, pk):
        try:
            domain = Domain.objects.get(name=pk)
            serializer = DomainSerializer(domain)
            return Response(serializer.data)
        except Domain.DoesNotExist:
            return Response({"error": "Domain not found"}, status=status.HTTP_404_NOT_FOUND)
