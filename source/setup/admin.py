from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from setup.default_setup import setup_default_settings
from setup.models import User


admin.site.register(User, UserAdmin)

setup_default_settings()






