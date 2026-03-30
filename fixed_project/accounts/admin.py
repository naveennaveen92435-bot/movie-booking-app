from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'city', 'dark_mode', 'is_blocked']
    list_filter = ['is_blocked', 'dark_mode']
