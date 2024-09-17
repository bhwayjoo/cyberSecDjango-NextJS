from django.urls import path
from .views import SubdomainSearch, DomainDetail

urlpatterns = [
    path('subdomain-search/', SubdomainSearch.as_view(), name='subdomain-search'),
    path('subdomain/<str:pk>/', DomainDetail.as_view(), name='subdomain-detail'),
]