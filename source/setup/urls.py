from django.urls import path
from setup.views import csrf

urlpatterns = [
    path('csrf/', csrf),
]
