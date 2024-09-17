from django.db import models

class Domain(models.Model):
    name = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=50, default="not_started")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Subdomain(models.Model):
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name='subdomains')
    name = models.CharField(max_length=255)
    ip = models.GenericIPAddressField(null=True, blank=True)
    status = models.CharField(max_length=50)
    gemini_analysis = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class OpenPort(models.Model):
    subdomain = models.ForeignKey(Subdomain, on_delete=models.CASCADE, related_name='open_ports')
    port = models.IntegerField()
    status = models.CharField(max_length=50)
    service = models.CharField(max_length=100)
    version = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.subdomain.name}:{self.port}"

class CrawledPage(models.Model):
    subdomain = models.ForeignKey(Subdomain, on_delete=models.CASCADE, related_name='crawled_pages')
    url = models.URLField()
    title = models.CharField(max_length=255)
    status_code = models.IntegerField()

    def __str__(self):
        return self.url

class Technology(models.Model):
    subdomain = models.ForeignKey(Subdomain, on_delete=models.CASCADE, related_name='technologies')
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name