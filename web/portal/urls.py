from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path(
        "google2aaa255fde4003d7.html",
        views.google_site_verification,
        name="google_site_verification",
    ),
    path("", views.HomeView.as_view(), name="home"),
    path("extract/", views.ExtractView.as_view(), name="extract"),
    path("download/<str:job_id>/", views.DownloadZipView.as_view(), name="download"),
]
