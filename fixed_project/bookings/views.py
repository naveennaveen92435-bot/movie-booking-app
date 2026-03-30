"""
Bookings App - Views
Seat selection, payment, ticket confirmation, profile, cancel
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

from movies.models import Show
from .models import SeatBooking, Booking, FoodItem, FoodOrder, Coupon, Notification
from .ai_recommender import suggest_seats


@login_required
def seat_selection(request, show_id):
    """
    Seat selection page with live layout, AI suggestions, food options.
    """
    show = get_object_or_404(Show, id=show_id, is_active=True)
    screen = show.screen

    # Release all expired holds first
    expired = SeatBooking.objects.filter(show=show, status='hold')
    for seat in expired:
        seat.release_if_expired()

    # Build full seat grid
    rows = [chr(65 + i) for i in range(screen.total_rows)]  # A, B, C...
    cols = list(range(1, screen.seats_per_row + 1))

    # Get all seat statuses
    seat_statuses = {}
    for sb in SeatBooking.objects.filter(show=show).select_related('held_by'):
        # Mark as available if hold expired
        if sb.status == 'hold' and sb.is_hold_expired():
            seat_statuses[sb.seat_label] = 'available'
        else:
            seat_statuses[sb.seat_label] = sb.status

    # Seat grid data for template
    seat_grid = []
    for row in rows:
        row_seats = []
        for col in cols:
            label = f"{row}{col}"
            status = seat_statuses.get(label, 'available')
            row_seats.append({'label': label, 'status': status})
        seat_grid.append({'row': row, 'seats': row_seats})

    # Food items
    food_items = FoodItem.objects.filter(is_available=True)

    # Active coupons (for display hint)
    coupons = Coupon.objects.filter(is_active=True)

    # AI seat suggestion
    ai_suggested = suggest_seats(show, num_seats=2, preference='center')

    context = {
        'show': show,
        'seat_grid': seat_grid,
        'food_items': food_items,
        'coupons': coupons,
        'ai_suggested': ai_suggested,
        'hold_minutes': 10,
    }
    return render(request, 'bookings/seat_selection.html', context)


@login_required
@require_POST
def hold_seats(request):
    """AJAX: Temporarily hold selected seats for the user"""
    data = json.loads(request.body)
    show_id = data.get('show_id')
    seat_labels = data.get('seats', [])

    show = get_object_or_404(Show, id=show_id)

    # Release any seats currently held by this user for this show
    SeatBooking.objects.filter(
        show=show, held_by=request.user, status='hold'
    ).update(status='available', held_by=None, held_at=None)

    held = []
    failed = []

    for label in seat_labels:
        # Check if seat is available
        seat_obj, created = SeatBooking.objects.get_or_create(
            show=show, seat_label=label,
            defaults={'row': label[0], 'col': int(label[1:]),
                      'status': 'available'}
        )
        # Refresh status
        if not created:
            seat_obj.release_if_expired()
            seat_obj.refresh_from_db()

        if seat_obj.status == 'available':
            seat_obj.status = 'hold'
            seat_obj.held_by = request.user
            seat_obj.held_at = timezone.now()
            seat_obj.save()
            held.append(label)
        else:
            failed.append(label)

    return JsonResponse({
        'held': held,
        'failed': failed,
        'expires_at': (timezone.now() + timezone.timedelta(minutes=10)).isoformat(),
    })


@login_required
def payment_page(request, show_id):
    """
    Payment page: shows order summary, payment options.
    """
    show = get_object_or_404(Show, id=show_id)

    # Get seats held by this user
    held_seats = SeatBooking.objects.filter(
        show=show, held_by=request.user, status='hold'
    )
    if not held_seats.exists():
        messages.error(request, 'No seats selected. Please select seats first.')
        return redirect('bookings:seat_selection', show_id=show_id)

    seat_labels = [s.seat_label for s in held_seats]
    num_seats = len(seat_labels)
    ticket_total = num_seats * float(show.ticket_price)

    # Food items from session or request
    food_items = FoodItem.objects.filter(is_available=True)

    context = {
        'show': show,
        'seat_labels': seat_labels,
        'num_seats': num_seats,
        'ticket_price': show.ticket_price,
        'ticket_total': ticket_total,
        'food_items': food_items,
        'hold_expires': (held_seats.first().held_at +
                         timezone.timedelta(minutes=10)).isoformat()
                         if held_seats.first().held_at else None,
    }
    return render(request, 'bookings/payment.html', context)


@login_required
@require_POST
def validate_coupon(request):
    """AJAX: Validate coupon code and return discount"""
    data = json.loads(request.body)
    code = data.get('code', '').strip().upper()
    amount = float(data.get('amount', 0))

    try:
        coupon = Coupon.objects.get(code=code)
        if coupon.is_valid():
            if amount < float(coupon.min_order_value):
                return JsonResponse({
                    'valid': False,
                    'message': f'Minimum order ₹{coupon.min_order_value} required'
                })
            discount = float(coupon.calculate_discount(amount))
            return JsonResponse({
                'valid': True,
                'discount': discount,
                'message': f'Coupon applied! You save ₹{discount:.2f}'
            })
        return JsonResponse({'valid': False, 'message': 'Coupon expired or invalid'})
    except Coupon.DoesNotExist:
        return JsonResponse({'valid': False, 'message': 'Invalid coupon code'})


@login_required
@require_POST
def confirm_booking(request):
    """
    Process booking: create Booking, FoodOrders, generate QR, send notification.
    """
    data = json.loads(request.body)
    show_id = data.get('show_id')
    payment_method = data.get('payment_method', 'upi')
    coupon_code = data.get('coupon_code', '')
    food_orders = data.get('food_orders', [])  # [{food_id, qty}]

    show = get_object_or_404(Show, id=show_id)

    # Get held seats
    held_seats = SeatBooking.objects.filter(
        show=show, held_by=request.user, status='hold'
    )
    if not held_seats.exists():
        return JsonResponse({'success': False, 'error': 'Session expired. Please re-select seats.'})

    seat_labels = [s.seat_label for s in held_seats]
    num_seats = len(seat_labels)
    ticket_total = num_seats * float(show.ticket_price)

    # Calculate food total
    food_total = 0
    food_items_to_create = []
    for fo in food_orders:
        try:
            item = FoodItem.objects.get(id=fo['food_id'], is_available=True)
            qty = int(fo.get('qty', 1))
            if qty > 0:
                food_total += float(item.price) * qty
                food_items_to_create.append((item, qty, float(item.price)))
        except FoodItem.DoesNotExist:
            pass

    # Apply coupon
    discount = 0
    coupon_obj = None
    if coupon_code:
        try:
            coupon_obj = Coupon.objects.get(code=coupon_code.upper())
            if coupon_obj.is_valid():
                discount = float(coupon_obj.calculate_discount(ticket_total + food_total))
                coupon_obj.used_count += 1
                coupon_obj.save()
        except Coupon.DoesNotExist:
            pass

    total_amount = ticket_total + food_total - discount

    # Create booking
    booking = Booking.objects.create(
        user=request.user,
        show=show,
        seats=','.join(seat_labels),
        num_seats=num_seats,
        ticket_price=ticket_total,
        food_total=food_total,
        discount_amount=discount,
        total_amount=total_amount,
        coupon=coupon_obj,
        payment_method=payment_method,
        payment_status='paid',
        status='confirmed',
    )

    # Create food orders
    for item, qty, price in food_items_to_create:
        FoodOrder.objects.create(booking=booking, food_item=item, quantity=qty, price=price)

    # Confirm seats
    held_seats.update(status='confirmed', booking=booking)

    # Generate QR code
    qr_data = f"BOOKING:{booking.booking_id}|USER:{request.user.username}|SHOW:{show.id}|SEATS:{','.join(seat_labels)}"
    qr_img = qrcode.make(qr_data)
    buffer = BytesIO()
    qr_img.save(buffer, format='PNG')
    booking.qr_code.save(f'qr_{booking.booking_id}.png',
                          ContentFile(buffer.getvalue()), save=True)

    # Create notification
    Notification.objects.create(
        user=request.user,
        title='Booking Confirmed!',
        message=f'Your booking for {show.movie.title} on {show.show_date} at {show.show_time} is confirmed. Seats: {", ".join(seat_labels)}',
        type='booking',
        booking=booking,
    )

    return JsonResponse({
        'success': True,
        'booking_id': str(booking.booking_id),
        'redirect': f'/bookings/ticket/{booking.booking_id}/',
    })


@login_required
def ticket_confirmation(request, booking_id):
    """
    Ticket confirmation page with QR code and booking details.
    """
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user)
    food_orders = booking.food_orders.select_related('food_item')

    context = {
        'booking': booking,
        'food_orders': food_orders,
        'seat_list': booking.get_seat_list(),
        'refund_policy': _get_refund_policy(booking),
    }
    return render(request, 'bookings/ticket_confirmation.html', context)


@login_required
@require_POST
def cancel_booking(request, booking_id):
    """Cancel booking and process refund"""
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user)

    if not booking.can_cancel():
        messages.error(request, 'This booking cannot be cancelled.')
        return redirect('accounts:profile')

    refund = booking.calculate_refund()

    # Update booking
    booking.status = 'cancelled'
    booking.cancelled_at = timezone.now()
    booking.refund_amount = refund
    booking.payment_status = 'refunded' if refund > 0 else 'paid'
    booking.save()

    # Release seats
    SeatBooking.objects.filter(booking=booking).update(
        status='available', booking=None, held_by=None
    )

    # Notify user
    Notification.objects.create(
        user=request.user,
        title='Booking Cancelled',
        message=f'Your booking for {booking.show.movie.title} has been cancelled. Refund of ₹{refund:.2f} will be processed in 5-7 days.',
        type='refund',
        booking=booking,
    )

    messages.success(request, f'Booking cancelled. Refund of ₹{refund:.2f} will be processed.')
    return redirect('accounts:profile')


@login_required
def ai_seat_suggestion_api(request, show_id):
    """AJAX: AI smart seat suggestion"""
    show = get_object_or_404(Show, id=show_id)
    num_seats = int(request.GET.get('num', 2))
    preference = request.GET.get('pref', 'center')

    suggested = suggest_seats(show, num_seats=num_seats, preference=preference)
    return JsonResponse({'suggested': suggested})


def _get_refund_policy(booking):
    """Build refund policy display for a booking"""
    if booking.status == 'cancelled':
        return f'Refund of ₹{booking.refund_amount:.2f} processed'
    from django.utils import timezone as tz
    show_dt = tz.datetime.combine(booking.show.show_date, booking.show.show_time)
    show_dt = tz.make_aware(show_dt)
    hours = (show_dt - tz.now()).total_seconds() / 3600
    if hours > 24:
        return '100% refund if cancelled 24+ hours before show'
    elif hours > 4:
        return '75% refund if cancelled 4-24 hours before show'
    elif hours > 1:
        return '50% refund if cancelled 1-4 hours before show'
    return 'No refund within 1 hour of show'
