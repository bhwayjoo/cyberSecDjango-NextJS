from rest_framework import serializers
from .models import Domain, Subdomain, OpenPort, CrawledPage, Technology

class OpenPortSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpenPort
        fields = ['port', 'status', 'service', 'version']

class CrawledPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrawledPage
        fields = ['url', 'title', 'status_code']

class TechnologySerializer(serializers.ModelSerializer):
    class Meta:
        model = Technology
        fields = ['name']

class SubdomainSerializer(serializers.ModelSerializer):
    open_ports = OpenPortSerializer(many=True, read_only=True)
    crawled_pages = CrawledPageSerializer(many=True, read_only=True)
    technologies = TechnologySerializer(many=True, read_only=True)

    class Meta:
        model = Subdomain
        fields = ['id', 'name', 'ip', 'status', 'open_ports', 'crawled_pages', 'technologies', 'gemini_analysis', 'created_at']

class DomainSerializer(serializers.ModelSerializer):
    subdomains = SubdomainSerializer(many=True, read_only=True)

    class Meta:
        model = Domain
        fields = ['id', 'name', 'subdomains', 'created_at', 'status']
