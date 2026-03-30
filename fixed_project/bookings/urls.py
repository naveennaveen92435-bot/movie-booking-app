"""Bookings app URL patterns"""

from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('select-seats/<int:show_id>/', views.seat_selection, name='seat_selection'),
    path('payment/<int:show_id>/', views.payment_page, name='payment'),
    path('ticket/<uuid:booking_id>/', views.ticket_confirmation, name='ticket_confirmation'),
    path('cancel/<uuid:booking_id>/', views.cancel_booking, name='cancel_booking'),

    # AJAX APIs
    path('api/hold-seats/', views.hold_seats, name='hold_seats'),
    path('api/validate-coupon/', views.validate_coupon, name='validate_coupon'),
    path('api/confirm/', views.confirm_booking, name='confirm_booking'),
    path('api/ai-seats/<int:show_id>/', views.ai_seat_suggestion_api, name='ai_seats'),
]
