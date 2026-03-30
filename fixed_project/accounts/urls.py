"""Accounts app URL patterns"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('api/toggle-dark-mode/', views.toggle_dark_mode, name='toggle_dark_mode'),
    path('api/mark-notifications-read/', views.mark_notifications_read,
         name='mark_notifications_read'),
    path('api/notifications/', views.notifications_api, name='notifications_api'),
]
