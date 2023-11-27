from django.urls import path
from .views import DownloadAppBuild

urlpatterns = [
    path("download/android_app/build_files", DownloadAppBuild.as_view(), name="download_app_build_zip"),
]
