from django.contrib import admin
from .models import Booking, SeatBooking, FoodItem, FoodOrder, Coupon, Notification


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'show', 'total_amount', 'status', 'payment_status', 'booked_at']
    list_filter = ['status', 'payment_status', 'booked_at']
    search_fields = ['user__username', 'user__email', 'show__movie__title']
    readonly_fields = ['booked_at', 'booking_id']
    list_editable = ['status', 'payment_status']
    date_hierarchy = 'booked_at'


@admin.register(SeatBooking)
class SeatBookingAdmin(admin.ModelAdmin):
    list_display = ['booking', 'seat_label', 'status']
    list_filter = ['status']
    search_fields = ['booking__user__username', 'seat_label']


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'is_available']
    list_filter = ['category', 'is_available']
    search_fields = ['name']
    list_editable = ['price', 'is_available']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'min_order_value', 'is_active', 'valid_to']
    list_filter = ['discount_type', 'is_active']
    search_fields = ['code']
    list_editable = ['is_active']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['user__username', 'title']
    list_editable = ['is_read']