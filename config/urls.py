"""
URL configuration for CricPulse Developer Portal.
"""

from django.contrib import admin
from django.urls import include, path
from apps.portal.views import healthz_view, llms_txt_view, robots_txt_view

admin.site.site_header = "CricPulse Operations Console"
admin.site.site_title = "CricPulse Admin"
admin.site.index_title = "Developer Platform & API Management"

urlpatterns = [
    path("healthz", healthz_view, name="healthz"),
    path("robots.txt", robots_txt_view, name="robots_txt"),
    path("llms.txt", llms_txt_view, name="llms_txt"),
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("", include("apps.portal.urls")),
]
