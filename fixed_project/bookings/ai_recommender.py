"""
AI Movie Recommender
Simple collaborative + content-based recommendation engine.
Uses user's booking history, preferred genres, and movie tags to score and rank movies.
"""

from django.db.models import Count


def get_recommendations(user, limit=6):
    """
    Get personalized movie recommendations for a user.
    Strategy:
    1. Get genres from past bookings
    2. Get user's preferred genres from profile
    3. Score all active movies using tag overlap + genre match
    4. Return top-N movies the user hasn't booked
    """
    from movies.models import Movie, Category
    from bookings.models import Booking

    # --- Step 1: Past booking genre signals ---
    past_bookings = Booking.objects.filter(
        user=user, status='confirmed'
    ).select_related('show__movie')

    booked_movie_ids = set()
    booked_genres = {}  # genre_slug -> count

    for booking in past_bookings:
        movie = booking.show.movie
        booked_movie_ids.add(movie.id)
        for cat in movie.categories.all():
            booked_genres[cat.slug] = booked_genres.get(cat.slug, 0) + 1

    # --- Step 2: Profile preferred genres ---
    preferred_genres = []
    try:
        preferred_genres = user.profile.get_preferred_genres_list()
    except Exception:
        pass

    for genre in preferred_genres:
        booked_genres[genre] = booked_genres.get(genre, 0) + 2  # Weight 2x

    # --- Step 3: Score all active movies not yet booked ---
    candidates = Movie.objects.filter(
        is_active=True
    ).exclude(id__in=booked_movie_ids).prefetch_related('categories')

    scored = []
    for movie in candidates:
        score = float(movie.imdb_score)  # Base score from IMDB rating

        # Genre match bonus
        for cat in movie.categories.all():
            if cat.slug in booked_genres:
                score += booked_genres[cat.slug] * 1.5

        # Featured bonus
        if movie.is_featured:
            score += 2

        scored.append((score, movie))

    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)

    return [movie for _, movie in scored[:limit]]


def suggest_seats(show, num_seats, preference='center'):
    """
    AI Smart Seat Suggestion.
    Returns best available seats based on preference.
    preference: 'center', 'front', 'back', 'aisle'
    """
    from bookings.models import SeatBooking

    # Get available seats
    booked_labels = set(
        SeatBooking.objects.filter(
            show=show, status__in=['confirmed', 'hold']
        ).values_list('seat_label', flat=True)
    )

    screen = show.screen
    rows = [chr(65 + i) for i in range(screen.total_rows)]  # A, B, C...
    cols = list(range(1, screen.seats_per_row + 1))

    # Build available seats grid
    all_available = []
    for row in rows:
        for col in cols:
            label = f"{row}{col}"
            if label not in booked_labels:
                all_available.append((row, col, label))

    if not all_available:
        return []

    # Score each seat by preference
    center_row = screen.total_rows // 2
    center_col = screen.seats_per_row // 2

    def score_seat(row_idx, col):
        row_i = ord(row_idx) - 65  # A=0, B=1...
        if preference == 'center':
            row_dist = abs(row_i - center_row)
            col_dist = abs(col - center_col)
            return -(row_dist + col_dist)  # Closer to center = higher score
        elif preference == 'front':
            return -row_i  # Lower row = better
        elif preference == 'back':
            return row_i  # Higher row = better
        elif preference == 'aisle':
            # Aisle = col 1 or last col
            return -(min(col - 1, screen.seats_per_row - col))
        return 0

    # Score and sort
    scored = [(score_seat(r, c), r, c, lbl) for r, c, lbl in all_available]
    scored.sort(reverse=True)

    # Find consecutive seats if num_seats > 1
    if num_seats == 1:
        return [scored[0][3]] if scored else []

    # Try to find consecutive seats in same row
    by_row = {}
    for _, r, c, lbl in scored:
        by_row.setdefault(r, []).append((c, lbl))

    best_group = None
    best_row_score = None

    for row_idx, seats_in_row in by_row.items():
        seats_in_row.sort()
        cols_in_row = [c for c, _ in seats_in_row]
        lbls_in_row = [l for _, l in seats_in_row]

        # Find consecutive run of num_seats
        for i in range(len(cols_in_row) - num_seats + 1):
            window = cols_in_row[i:i + num_seats]
            if window[-1] - window[0] == num_seats - 1:  # Consecutive
                group = lbls_in_row[i:i + num_seats]
                rs = score_seat(row_idx, window[num_seats // 2])
                if best_row_score is None or rs > best_row_score:
                    best_row_score = rs
                    best_group = group

    if best_group:
        return best_group

    # Fallback: return top-N individual seats
    return [scored[i][3] for i in range(min(num_seats, len(scored)))]
