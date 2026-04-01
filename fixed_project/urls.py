"""
Smart AI Movie Booking System - Main URL Configuration
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),           # Django built-in admin
    path('', include('movies.urls')),                  # Homepage & movies
    path('bookings/', include('bookings.urls')),       # Booking flow
    path('accounts/', include('accounts.urls')),       # Auth & profile
    path('admin-panel/', include('admin_panel.urls')), # Custom admin dashboard
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)