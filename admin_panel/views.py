"""
Admin Panel - Views
Dashboard, Movie/Theatre/Screen/Show management, Bookings, Users, Reports
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.views.decorators.http import require_POST
import json
from datetime import timedelta

from movies.models import Movie, Category, Theatre, Screen, Show
from bookings.models import Booking, SeatBooking, FoodItem, Coupon, Notification
from accounts.models import UserProfile


def is_admin(user):
    """Check if user is staff/admin"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


admin_required = user_passes_test(is_admin, login_url='/accounts/login/')


@login_required
@admin_required
def dashboard(request):
    """
    Admin dashboard with KPIs and charts data
    """
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # KPI stats
    total_bookings = Booking.objects.filter(status='confirmed').count()
    total_revenue = Booking.objects.filter(
        status='confirmed', payment_status='paid'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    active_movies = Movie.objects.filter(is_active=True).count()
    total_users = User.objects.filter(is_staff=False).count()

    # Today's stats
    today_bookings = Booking.objects.filter(
        status='confirmed', booked_at__date=today
    ).count()
    today_revenue = Booking.objects.filter(
        status='confirmed', payment_status='paid', booked_at__date=today
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    # Daily revenue last 7 days (for chart)
    daily_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        rev = Booking.objects.filter(
            status='confirmed', payment_status='paid', booked_at__date=day
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        daily_data.append({
            'date': day.strftime('%b %d'),
            'revenue': float(rev),
            'bookings': Booking.objects.filter(
                status='confirmed', booked_at__date=day
            ).count()
        })

    # Top 5 movies by bookings
    top_movies = Movie.objects.filter(
        shows__bookings__status='confirmed'
    ).annotate(
        booking_count=Count('shows__bookings')
    ).order_by('-booking_count')[:5]

    # Recent bookings
    recent_bookings = Booking.objects.select_related(
        'user', 'show__movie'
    ).order_by('-booked_at')[:10]

    context = {
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'active_movies': active_movies,
        'total_users': total_users,
        'today_bookings': today_bookings,
        'today_revenue': today_revenue,
        'daily_data': json.dumps(daily_data),
        'top_movies': top_movies,
        'recent_bookings': recent_bookings,
    }
    return render(request, 'admin_panel/dashboard.html', context)


# ─── Movie Management ───────────────────────────────────────────────────────

@login_required
@admin_required
def movie_list(request):
    movies = Movie.objects.prefetch_related('categories').order_by('-created_at')
    return render(request, 'admin_panel/movie_list.html', {'movies': movies})


@login_required
@admin_required
def movie_add(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        try:
            movie = Movie(
                title=request.POST['title'],
                slug=request.POST['slug'],
                description=request.POST['description'],
                cast=request.POST['cast'],
                director=request.POST['director'],
                duration_minutes=int(request.POST['duration_minutes']),
                release_date=request.POST['release_date'],
                language=request.POST.get('language', 'english'),
                rating=request.POST.get('rating', 'UA'),
                imdb_score=float(request.POST.get('imdb_score', 7.0)),
                poster_url=request.POST.get('poster_url', ''),
                trailer_url=request.POST.get('trailer_url', ''),
                tags=request.POST.get('tags', ''),
                is_featured=bool(request.POST.get('is_featured')),
            )
            if 'poster' in request.FILES:
                movie.poster = request.FILES['poster']
            movie.save()
            selected_cats = request.POST.getlist('categories')
            movie.categories.set(selected_cats)
            messages.success(request, f'Movie "{movie.title}" added successfully.')
            return redirect('admin_panel:movie_list')
        except Exception as e:
            messages.error(request, f'Error: {e}')

    return render(request, 'admin_panel/movie_form.html',
                  {'categories': categories, 'action': 'Add'})


@login_required
@admin_required
def movie_edit(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    categories = Category.objects.all()
    if request.method == 'POST':
        try:
            movie.title = request.POST['title']
            movie.slug = request.POST['slug']
            movie.description = request.POST['description']
            movie.cast = request.POST['cast']
            movie.director = request.POST['director']
            movie.duration_minutes = int(request.POST['duration_minutes'])
            movie.release_date = request.POST['release_date']
            movie.language = request.POST.get('language', movie.language)
            movie.rating = request.POST.get('rating', movie.rating)
            movie.imdb_score = float(request.POST.get('imdb_score', movie.imdb_score))
            movie.poster_url = request.POST.get('poster_url', movie.poster_url)
            movie.trailer_url = request.POST.get('trailer_url', movie.trailer_url)
            movie.tags = request.POST.get('tags', movie.tags)
            movie.is_featured = bool(request.POST.get('is_featured'))
            movie.is_active = bool(request.POST.get('is_active'))
            if 'poster' in request.FILES:
                movie.poster = request.FILES['poster']
            movie.save()
            movie.categories.set(request.POST.getlist('categories'))
            messages.success(request, 'Movie updated.')
            return redirect('admin_panel:movie_list')
        except Exception as e:
            messages.error(request, f'Error: {e}')

    return render(request, 'admin_panel/movie_form.html',
                  {'movie': movie, 'categories': categories, 'action': 'Edit'})


@login_required
@admin_required
@require_POST
def movie_delete(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    movie.is_active = False
    movie.save()
    messages.success(request, f'Movie "{movie.title}" deactivated.')
    return redirect('admin_panel:movie_list')


# ─── Theatre & Screen Management ────────────────────────────────────────────

@login_required
@admin_required
def theatre_list(request):
    theatres = Theatre.objects.prefetch_related('screens').all()
    return render(request, 'admin_panel/theatre_list.html', {'theatres': theatres})


@login_required
@admin_required
def theatre_add(request):
    if request.method == 'POST':
        Theatre.objects.create(
            name=request.POST['name'],
            location=request.POST['location'],
            city=request.POST['city'],
        )
        messages.success(request, 'Theatre added.')
        return redirect('admin_panel:theatre_list')
    return render(request, 'admin_panel/theatre_form.html', {'action': 'Add'})


@login_required
@admin_required
def screen_add(request, theatre_id):
    theatre = get_object_or_404(Theatre, id=theatre_id)
    if request.method == 'POST':
        Screen.objects.create(
            theatre=theatre,
            name=request.POST['name'],
            total_rows=int(request.POST.get('total_rows', 8)),
            seats_per_row=int(request.POST.get('seats_per_row', 10)),
        )
        messages.success(request, 'Screen added.')
        return redirect('admin_panel:theatre_list')
    return render(request, 'admin_panel/screen_form.html',
                  {'theatre': theatre, 'action': 'Add'})


# ─── Show Management ─────────────────────────────────────────────────────────

@login_required
@admin_required
def show_list(request):
    today = timezone.now().date()
    shows = Show.objects.filter(
        show_date__gte=today
    ).select_related('movie', 'screen__theatre').order_by('show_date', 'show_time')
    return render(request, 'admin_panel/show_list.html', {'shows': shows})


@login_required
@admin_required
def show_add(request):
    movies = Movie.objects.filter(is_active=True)
    screens = Screen.objects.filter(is_active=True).select_related('theatre')
    if request.method == 'POST':
        try:
            Show.objects.create(
                movie_id=request.POST['movie'],
                screen_id=request.POST['screen'],
                show_date=request.POST['show_date'],
                show_time=request.POST['show_time'],
                ticket_price=float(request.POST.get('ticket_price', 200)),
            )
            messages.success(request, 'Show scheduled.')
            return redirect('admin_panel:show_list')
        except Exception as e:
            messages.error(request, f'Error: {e}')
    return render(request, 'admin_panel/show_form.html',
                  {'movies': movies, 'screens': screens})


# ─── Booking Management ──────────────────────────────────────────────────────

@login_required
@admin_required
def booking_list(request):
    status_filter = request.GET.get('status', '')
    bookings = Booking.objects.select_related(
        'user', 'show__movie'
    ).order_by('-booked_at')

    if status_filter:
        bookings = bookings.filter(status=status_filter)

    return render(request, 'admin_panel/booking_list.html',
                  {'bookings': bookings, 'status_filter': status_filter})


@login_required
@admin_required
@require_POST
def admin_cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)
    if booking.status == 'confirmed':
        refund = booking.calculate_refund()
        booking.status = 'cancelled'
        booking.refund_amount = refund
        booking.cancelled_at = timezone.now()
        booking.payment_status = 'refunded' if refund > 0 else booking.payment_status
        booking.save()
        SeatBooking.objects.filter(booking=booking).update(
            status='available', booking=None
        )
        Notification.objects.create(
            user=booking.user,
            title='Booking Cancelled by Admin',
            message=f'Your booking for {booking.show.movie.title} was cancelled. Refund: ₹{refund:.2f}',
            type='refund', booking=booking,
        )
        messages.success(request, f'Booking cancelled. Refund: ₹{refund:.2f}')
    return redirect('admin_panel:booking_list')


# ─── User Management ─────────────────────────────────────────────────────────

@login_required
@admin_required
def user_list(request):
    users = User.objects.filter(is_staff=False).select_related('profile').annotate(
        booking_count=Count('bookings')
    ).order_by('-date_joined')
    return render(request, 'admin_panel/user_list.html', {'users': users})


@login_required
@admin_required
@require_POST
def toggle_user_block(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.is_blocked = not profile.is_blocked
    profile.save()
    status = 'blocked' if profile.is_blocked else 'unblocked'
    messages.success(request, f'User {user.username} has been {status}.')
    return redirect('admin_panel:user_list')


# ─── Food & Coupon Management ────────────────────────────────────────────────

@login_required
@admin_required
def food_list(request):
    foods = FoodItem.objects.all()
    coupons = Coupon.objects.all()
    return render(request, 'admin_panel/food_list.html',
                  {'foods': foods, 'coupons': coupons})


@login_required
@admin_required
@require_POST
def food_add(request):
    FoodItem.objects.create(
        name=request.POST['name'],
        category=request.POST.get('category', 'snacks'),
        price=float(request.POST['price']),
        description=request.POST.get('description', ''),
    )
    messages.success(request, 'Food item added.')
    return redirect('admin_panel:food_list')


@login_required
@admin_required
@require_POST
def coupon_add(request):
    Coupon.objects.create(
        code=request.POST['code'].strip().upper(),
        discount_type=request.POST['discount_type'],
        discount_value=float(request.POST['discount_value']),
        min_order_value=float(request.POST.get('min_order_value', 0)),
        max_discount=float(request.POST.get('max_discount', 500)),
        valid_from=request.POST['valid_from'],
        valid_to=request.POST['valid_to'],
        usage_limit=int(request.POST.get('usage_limit', 100)),
    )
    messages.success(request, 'Coupon created.')
    return redirect('admin_panel:food_list')


# ─── Reports / Analytics ─────────────────────────────────────────────────────

@login_required
@admin_required
def reports(request):
    today = timezone.now().date()

    # Monthly revenue last 12 months
    monthly_data = []
    for i in range(11, -1, -1):
        month_start = (today.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        month_end = (month_start + timedelta(days=31)).replace(day=1)
        rev = Booking.objects.filter(
            status='confirmed', payment_status='paid',
            booked_at__date__gte=month_start,
            booked_at__date__lt=month_end,
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'revenue': float(rev),
        })

    # Most booked movies
    top_movies = Movie.objects.filter(
        shows__bookings__status='confirmed'
    ).annotate(
        booking_count=Count('shows__bookings'),
        revenue=Sum('shows__bookings__total_amount'),
    ).order_by('-booking_count')[:10]

    # Payment method distribution
    payment_dist = Booking.objects.filter(status='confirmed').values(
        'payment_method'
    ).annotate(count=Count('id'))

    # Category popularity
    cat_popularity = Category.objects.annotate(
        booking_count=Count('movies__shows__bookings',
                            filter=Q(movies__shows__bookings__status='confirmed'))
    ).order_by('-booking_count')

    context = {
        'monthly_data': json.dumps(monthly_data),
        'top_movies': top_movies,
        'payment_dist': list(payment_dist),
        'cat_popularity': cat_popularity,
        'total_revenue': Booking.objects.filter(
            status='confirmed', payment_status='paid'
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
    }
    return render(request, 'admin_panel/reports.html', context)
