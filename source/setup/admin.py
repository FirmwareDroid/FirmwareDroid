from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from setup.default_setup import setup_application_setting, setup_file_store_setting
from setup.models import User


admin.site.register(User, UserAdmin)

setup_application_setting()
setup_file_store_setting()





