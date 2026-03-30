"""Admin panel URL patterns"""

from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    # Movies
    path('movies/', views.movie_list, name='movie_list'),
    path('movies/add/', views.movie_add, name='movie_add'),
    path('movies/edit/<int:movie_id>/', views.movie_edit, name='movie_edit'),
    path('movies/delete/<int:movie_id>/', views.movie_delete, name='movie_delete'),

    # Theatres & Screens
    path('theatres/', views.theatre_list, name='theatre_list'),
    path('theatres/add/', views.theatre_add, name='theatre_add'),
    path('theatres/<int:theatre_id>/screen/add/', views.screen_add, name='screen_add'),

    # Shows
    path('shows/', views.show_list, name='show_list'),
    path('shows/add/', views.show_add, name='show_add'),

    # Bookings
    path('bookings/', views.booking_list, name='booking_list'),
    path('bookings/cancel/<uuid:booking_id>/', views.admin_cancel_booking,
         name='cancel_booking'),

    # Users
    path('users/', views.user_list, name='user_list'),
    path('users/toggle-block/<int:user_id>/', views.toggle_user_block,
         name='toggle_user_block'),

    # Food & Coupons
    path('food/', views.food_list, name='food_list'),
    path('food/add/', views.food_add, name='food_add'),
    path('food/coupon/add/', views.coupon_add, name='coupon_add'),

    # Reports
    path('reports/', views.reports, name='reports'),
]
