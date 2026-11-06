from django.urls import path
from . import views

app_name = "portal"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("pricing/", views.pricing_view, name="pricing"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("keys/create/", views.create_key_view, name="create_key"),
    path("keys/<int:key_id>/revoke/", views.revoke_key_view, name="revoke_key"),
    path("docs/", views.docs_view, name="docs"),
    path("api/internal/verify-key/", views.verify_key_internal_view, name="internal_verify_key"),
]
