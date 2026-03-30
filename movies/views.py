"""
Movies App - Views
Homepage, movie detail, show listings, city movies API
"""

from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .models import Movie, Category, Show
from bookings.ai_recommender import get_recommendations
import random


def homepage(request):
    """
    Homepage: Movie grid with categories + AI recommendations
    """
    category_slug = request.GET.get('category', 'all')
    search_query  = request.GET.get('q', '')
    selected_city = request.GET.get('city', '')

    movies = Movie.objects.filter(is_active=True)

    # Filter by category
    if category_slug and category_slug != 'all':
        movies = movies.filter(categories__slug=category_slug)

    # Filter by search
    if search_query:
        movies = movies.filter(
            Q(title__icontains=search_query) |
            Q(cast__icontains=search_query)  |
            Q(director__icontains=search_query)
        )

    # ── FIXED: City filter checks both city field AND location field ──────────
    # This ensures "Amalapuram" AND "East Godavari" both return correct results
    if selected_city:
        today = timezone.now().date()
        city_movie_ids = Show.objects.filter(
            Q(screen__theatre__city__iexact=selected_city) |
            Q(screen__theatre__location__icontains=selected_city),
            show_date__gte=today,
            is_active=True,
        ).values_list('movie_id', flat=True).distinct()

        movies = movies.filter(id__in=city_movie_ids)

    movies = movies.distinct()

    # Featured movies for hero section
    featured = Movie.objects.filter(is_active=True, is_featured=True)[:5]

    # All categories
    categories = Category.objects.all()

    # AI recommendations
    if request.user.is_authenticated:
        ai_recommendations = get_recommendations(request.user, limit=6)
    else:
        ai_recommendations = Movie.objects.filter(
            is_active=True
        ).order_by('-imdb_score')[:6]

    context = {
        'movies':            movies,
        'featured':          featured,
        'categories':        categories,
        'active_category':   category_slug,
        'search_query':      search_query,
        'ai_recommendations': ai_recommendations,
        'selected_city':     selected_city,
    }
    return render(request, 'movies/homepage.html', context)


def movie_detail(request, slug):
    """
    Movie detail page: description, cast, trailer, shows
    """
    movie = get_object_or_404(Movie, slug=slug, is_active=True)

    today         = timezone.now().date()
    selected_city = request.GET.get('city', '')

    # ── FIXED: Shows query ────────────────────────────────────────────────────
    shows_qs = Show.objects.filter(
        movie=movie,
        is_active=True,
        show_date__gte=today,
    ).select_related('screen__theatre').order_by('show_date', 'show_time')

    # ── FIXED: City filter checks both city field AND location field ──────────
    # Searching "East Godavari" now also returns Amalapuram theatre shows
    if selected_city:
        shows_qs = shows_qs.filter(
            Q(screen__theatre__city__iexact=selected_city) |
            Q(screen__theatre__location__icontains=selected_city)
        )

    # Group shows by date
    shows_by_date = {}
    for show in shows_qs:
        date_key = show.show_date
        if date_key not in shows_by_date:
            shows_by_date[date_key] = []
        shows_by_date[date_key].append(show)

    # Similar movies (same category)
    similar = Movie.objects.filter(
        categories__in=movie.categories.all(),
        is_active=True
    ).exclude(id=movie.id).distinct()[:6]

    context = {
        'movie':         movie,
        'shows_by_date': shows_by_date,
        'similar':       similar,
        'cast_list':     movie.get_cast_list(),
        'selected_city': selected_city,
    }
    return render(request, 'movies/movie_detail.html', context)


def movie_search_api(request):
    """
    AJAX search endpoint for live search
    """
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})

    movies = Movie.objects.filter(
        Q(title__icontains=query) | Q(cast__icontains=query),
        is_active=True
    )[:8]

    results = [{
        'id':     m.id,
        'title':  m.title,
        'slug':   m.slug,
        'poster': m.get_poster_url(),
        'rating': str(m.imdb_score),
        'genre':  ', '.join(c.get_name_display() for c in m.categories.all()),
    } for m in movies]

    return JsonResponse({'results': results})


def movies_by_city_api(request):
    """
    AJAX: Returns movies that have actual upcoming shows in the selected city.
    FIXED: Also checks location field so East Godavari returns Amalapuram results.
    """
    city  = request.GET.get('city', 'Hyderabad')
    today = timezone.now().date()

    # ── FIXED: Check both city and location fields ────────────────────────────
    city_movie_ids = Show.objects.filter(
        Q(screen__theatre__city__iexact=city) |
        Q(screen__theatre__location__icontains=city),
        show_date__gte=today,
        is_active=True,
    ).values_list('movie_id', flat=True).distinct()

    city_movies = Movie.objects.filter(
        id__in=city_movie_ids,
        is_active=True,
    ).distinct()

    if not city_movies.exists():
        return JsonResponse({
            'movies':  [],
            'city':    city,
            'message': f'No shows available in {city} currently.',
        })

    results = [{
        'id':     m.id,
        'title':  m.title,
        'slug':   m.slug,
        'poster': m.get_poster_url(),
        'rating': str(m.imdb_score),
        'genre':  ', '.join(
            c.get_name_display() for c in m.categories.all()[:2]
        ),
    } for m in city_movies]

    return JsonResponse({'movies': results, 'city': city})


def seat_heatmap_api(request, show_id):
    """
    Live seat availability heatmap data.
    """
    from bookings.models import SeatBooking

    show = get_object_or_404(Show, id=show_id)

    # Release expired holds first
    expired_holds = SeatBooking.objects.filter(show=show, status='hold')
    for seat in expired_holds:
        seat.release_if_expired()

    seats    = SeatBooking.objects.filter(show=show).values('seat_label', 'status')
    seat_map = {s['seat_label']: s['status'] for s in seats}

    return JsonResponse({
        'seat_map':  seat_map,
        'available': show.available_seats_count(),
        'total':     show.screen.total_seats,
        'occupancy': show.occupancy_percentage(),
    })