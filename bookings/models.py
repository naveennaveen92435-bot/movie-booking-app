"""
Bookings App - Models
Defines: SeatBooking, Booking, Payment, FoodItem, FoodOrder, Coupon
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from movies.models import Show
import uuid


class SeatBooking(models.Model):
    """Individual seat status for a show"""
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('hold', 'Hold'),         # Temporary lock during checkout
        ('confirmed', 'Confirmed'),
    ]
    show = models.ForeignKey(Show, on_delete=models.CASCADE, related_name='seat_bookings')
    seat_label = models.CharField(max_length=10)  # e.g., "A1", "B3"
    row = models.CharField(max_length=5)
    col = models.PositiveIntegerField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')
    held_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='held_seats')
    held_at = models.DateTimeField(null=True, blank=True)
    booking = models.ForeignKey('Booking', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='seat_bookings')

    class Meta:
        unique_together = ['show', 'seat_label']

    def __str__(self):
        return f"{self.show} - Seat {self.seat_label} ({self.status})"

    def is_hold_expired(self, hold_minutes=10):
        """Check if hold timer has expired"""
        if self.status == 'hold' and self.held_at:
            expiry = self.held_at + timezone.timedelta(minutes=hold_minutes)
            return timezone.now() > expiry
        return False

    def release_if_expired(self):
        """Auto-release seat if hold expired"""
        if self.is_hold_expired():
            self.status = 'available'
            self.held_by = None
            self.held_at = None
            self.save()
            return True
        return False


class FoodItem(models.Model):
    """Snacks & food available for pre-booking"""
    CATEGORY_CHOICES = [
        ('snacks', 'Snacks'),
        ('drinks', 'Drinks'),
        ('combos', 'Combos'),
    ]
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='snacks')
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.CharField(max_length=200, blank=True)
    image_url = models.URLField(blank=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - ₹{self.price}"


class Coupon(models.Model):
    """Discount coupon codes"""
    code = models.CharField(max_length=20, unique=True)
    discount_type = models.CharField(max_length=10,
                                     choices=[('percent', 'Percent'), ('flat', 'Flat Amount')])
    discount_value = models.DecimalField(max_digits=8, decimal_places=2)
    min_order_value = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    max_discount = models.DecimalField(max_digits=8, decimal_places=2, default=500)
    valid_from = models.DateField()
    valid_to = models.DateField()
    usage_limit = models.PositiveIntegerField(default=100)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.discount_value}{'%' if self.discount_type == 'percent' else '₹'}"

    def is_valid(self):
        today = timezone.now().date()
        return (self.is_active and
                self.valid_from <= today <= self.valid_to and
                self.used_count < self.usage_limit)

    def calculate_discount(self, amount):
        if self.discount_type == 'percent':
            disc = amount * self.discount_value / 100
            return min(disc, self.max_discount)
        return min(self.discount_value, amount)


class Booking(models.Model):
    """A complete booking record"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('upi', 'UPI'),
        ('card', 'Card'),
        ('cash', 'Cash'),
    ]

    booking_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    show = models.ForeignKey(Show, on_delete=models.CASCADE, related_name='bookings')
    seats = models.CharField(max_length=500)  # Comma-separated seat labels
    num_seats = models.PositiveIntegerField(default=1)
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2)
    food_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES,
                                      default='upi')
    payment_status = models.CharField(max_length=20,
                                      choices=[('pending','Pending'),('paid','Paid'),
                                               ('failed','Failed'),('refunded','Refunded')],
                                      default='pending')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    booked_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-booked_at']

    def __str__(self):
        return f"Booking {self.booking_id} | {self.user.username} | {self.show.movie.title}"

    def get_seat_list(self):
        return [s.strip() for s in self.seats.split(',') if s.strip()]

    def can_cancel(self):
        """Allow cancel if show hasn't started"""
        show_datetime = timezone.datetime.combine(
            self.show.show_date, self.show.show_time
        )
        show_datetime = timezone.make_aware(show_datetime)
        return self.status == 'confirmed' and timezone.now() < show_datetime

    def calculate_refund(self):
        """Calculate refund based on cancellation timing"""
        show_datetime = timezone.datetime.combine(
            self.show.show_date, self.show.show_time
        )
        show_datetime = timezone.make_aware(show_datetime)
        hours_left = (show_datetime - timezone.now()).total_seconds() / 3600

        if hours_left > 24:
            return self.total_amount  # Full refund
        elif hours_left > 4:
            return self.total_amount * 0.75  # 75% refund
        elif hours_left > 1:
            return self.total_amount * 0.50  # 50% refund
        return 0  # No refund within 1 hour


class FoodOrder(models.Model):
    """Food items ordered with a booking"""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='food_orders')
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.food_item.name} x{self.quantity}"

    @property
    def subtotal(self):
        return self.price * self.quantity


class Notification(models.Model):
    """User notifications"""
    TYPE_CHOICES = [
        ('booking', 'Booking'),
        ('reminder', 'Reminder'),
        ('refund', 'Refund'),
        ('offer', 'Offer'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='booking')
    is_read = models.BooleanField(default=False)
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"
