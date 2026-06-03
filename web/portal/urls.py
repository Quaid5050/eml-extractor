from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("extract/", views.ExtractView.as_view(), name="extract"),
    path("download/<str:job_id>/", views.DownloadZipView.as_view(), name="download"),
]
