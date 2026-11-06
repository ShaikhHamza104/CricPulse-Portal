from django.urls import path
from . import views

app_name = "analytics"

urlpatterns = [
    path("", views.showcase_view, name="showcase"),
    path("proxy/", views.live_query_proxy, name="proxy"),
]
