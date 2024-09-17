from django.contrib import admin
from .models import Domain, Subdomain, OpenPort, CrawledPage, Technology

# Inline for OpenPort to be displayed within Subdomain admin
class OpenPortInline(admin.TabularInline):
    model = OpenPort
    extra = 1

# Inline for CrawledPage to be displayed within Subdomain admin
class CrawledPageInline(admin.TabularInline):
    model = CrawledPage
    extra = 1

# Inline for Technology to be displayed within Subdomain admin
class TechnologyInline(admin.TabularInline):
    model = Technology
    extra = 1

# Subdomain Admin with inlines for OpenPort, CrawledPage, and Technology
@admin.register(Subdomain)
class SubdomainAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'domain', 'status', 'created_at')
    search_fields = ('name', 'domain__name', 'ip')
    list_filter = ('status', 'created_at')
    inlines = [OpenPortInline, CrawledPageInline, TechnologyInline]

# Domain Admin
@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)

# OpenPort Admin (If you want to manage OpenPort directly)
@admin.register(OpenPort)
class OpenPortAdmin(admin.ModelAdmin):
    list_display = ('id', 'subdomain', 'port', 'status', 'service', 'version')
    search_fields = ('subdomain__name', 'port', 'service')
    list_filter = ('status', 'service')

# CrawledPage Admin (If you want to manage CrawledPage directly)
@admin.register(CrawledPage)
class CrawledPageAdmin(admin.ModelAdmin):
    list_display = ('id', 'subdomain', 'url', 'title', 'status_code')
    search_fields = ('subdomain__name', 'url', 'title')
    list_filter = ('status_code',)

# Technology Admin (If you want to manage Technology directly)
@admin.register(Technology)
class TechnologyAdmin(admin.ModelAdmin):
    list_display = ('id', 'subdomain', 'name')
    search_fields = ('subdomain__name', 'name')
    list_filter = ('name',)
