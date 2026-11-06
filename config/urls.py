"""
URL configuration for CricPulse Developer Portal.
"""

from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "CricPulse Operations Console"
admin.site.site_title = "CricPulse Admin"
admin.site.index_title = "Developer Platform & API Management"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("", include("apps.portal.urls")),
]
