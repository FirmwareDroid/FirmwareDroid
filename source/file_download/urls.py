from django.urls import path
from .views import DownloadAppBuildView
from rest_framework import routers

# router = routers.SimpleRouter()
# router.register('download/', DownloadAppBuildViewSet, basename="download")
# urlpatterns = router.urls


urlpatterns = [
    path("download/android_app/build_files", DownloadAppBuildView.as_view({'post': 'download'}))
]
