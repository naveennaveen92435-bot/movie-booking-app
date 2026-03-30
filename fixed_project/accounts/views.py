"""
Accounts App - Views
Register, login, logout, profile, dark mode toggle, notifications
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import UserProfile
from bookings.models import Booking, Notification


def register_view(request):
    if request.user.is_authenticated:
        return redirect('movies:homepage')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')
        phone = request.POST.get('phone', '').strip()

        if not username or not email or not password:
            messages.error(request, 'All fields are required.')
        elif password != confirm:
            messages.error(request, 'Passwords do not match.')
        elif len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            UserProfile.objects.create(user=user, phone=phone)
            login(request, user)
            messages.success(request, f'Welcome, {username}!')
            return redirect('movies:homepage')

    return render(request, 'accounts/register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('movies:homepage')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('movies:homepage')
        else:
            messages.error(request, 'Invalid credentials')

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('movies:homepage')


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    bookings = Booking.objects.filter(
        user=request.user
    ).select_related('show__movie', 'show__screen__theatre').order_by('-booked_at')

    active_bookings = bookings.filter(status='confirmed')
    past_bookings = bookings.exclude(status='confirmed')

    # ✅ FIXED (NO slice here)
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')

    context = {
        'profile': profile,
        'active_bookings': active_bookings,
        'past_bookings': past_bookings,

        # ✅ slice here only
        'notifications': notifications[:10],

        # ✅ filter before slice
        'unread_count': notifications.filter(is_read=False).count(),

        'genre_choices': [
            ('action','Action'),('crime','Crime'),('family','Family'),
            ('horror','Horror'),('comedy','Comedy'),('drama','Drama'),
            ('thriller','Thriller'),('sci-fi','Sci-Fi'),('romance','Romance'),
        ],
    }

    return render(request, 'accounts/profile.html', context)


@login_required
@require_POST
def update_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    profile.phone = request.POST.get('phone', profile.phone)
    profile.city = request.POST.get('city', profile.city)

    genres = request.POST.getlist('preferred_genres')
    profile.preferred_genres = ','.join(genres)
    profile.save()

    request.user.email = request.POST.get('email', request.user.email)
    request.user.first_name = request.POST.get('first_name', request.user.first_name)
    request.user.last_name = request.POST.get('last_name', request.user.last_name)
    request.user.save()

    messages.success(request, 'Profile updated')
    return redirect('accounts:profile')


@login_required
@require_POST
def toggle_dark_mode(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile.dark_mode = not profile.dark_mode
    profile.save()
    return JsonResponse({'dark_mode': profile.dark_mode})


@login_required
@require_POST
def mark_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})


@login_required
def notifications_api(request):
    # ✅ FIXED
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')

    unread = notifs.filter(is_read=False).count()

    notifs = notifs[:15]

    data = [{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'type': n.type,
        'is_read': n.is_read,
        'created_at': n.created_at.strftime('%d %b %Y %H:%M'),
    } for n in notifs]

    return JsonResponse({'notifications': data, 'unread': unread})