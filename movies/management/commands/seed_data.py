"""
Management command: seed_data
Usage: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from datetime import timedelta, date, time
import random

from movies.models import Category, Movie, Theatre, Screen, Show
from bookings.models import FoodItem, Coupon
from accounts.models import UserProfile


MOVIES_DATA = [
    {
        "title": "The Godfather",
        "director": "Francis Ford Coppola",
        "cast": "Marlon Brando, Al Pacino, James Caan",
        "desc": "The aging patriarch of an organized crime dynasty transfers control to his reluctant son.",
        "year": 1972, "duration": 175, "imdb": 9.2, "rating": "A", "lang": "english",
        "categories": ["crime"],
        "poster": "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsLeFJQ3BbfYD.jpg",
        "trailer": "https://www.youtube.com/embed/sY1S34973zA",
        "tags": "mafia,family,loyalty,power,classic", "featured": True,
    },
    {
        "title": "The Dark Knight",
        "director": "Christopher Nolan",
        "cast": "Christian Bale, Heath Ledger, Aaron Eckhart",
        "desc": "Batman must accept one of the greatest tests of his ability to fight injustice when the Joker unleashes chaos on Gotham.",
        "year": 2008, "duration": 152, "imdb": 9.0, "rating": "UA", "lang": "english",
        "categories": ["action"],
        "poster": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
        "trailer": "https://www.youtube.com/embed/EXeTwQWrcwY",
        "tags": "batman,joker,gotham,superhero,villain", "featured": True,
    },
    {
        "title": "Inception",
        "director": "Christopher Nolan",
        "cast": "Leonardo DiCaprio, Joseph Gordon-Levitt, Elliot Page",
        "desc": "A thief who steals corporate secrets through dream-sharing technology is given the inverse task of planting an idea.",
        "year": 2010, "duration": 148, "imdb": 8.8, "rating": "UA", "lang": "english",
        "categories": ["thriller", "sci_fi"],
        "poster": "https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg",
        "trailer": "https://www.youtube.com/embed/YoHD9XEInc0",
        "tags": "dreams,heist,mind,layers,nolan", "featured": True,
    },
    {
        "title": "Oppenheimer",
        "director": "Christopher Nolan",
        "cast": "Cillian Murphy, Emily Blunt, Robert Downey Jr.",
        "desc": "The story of J. Robert Oppenheimer's role in the development of the atomic bomb during World War II.",
        "year": 2023, "duration": 180, "imdb": 8.9, "rating": "UA", "lang": "english",
        "categories": ["thriller"],
        "poster": "https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg",
        "trailer": "https://www.youtube.com/embed/uYPbbksJxIg",
        "tags": "atomic,bomb,war,scientist,history", "featured": True,
    },
    {
        "title": "Dune: Part Two",
        "director": "Denis Villeneuve",
        "cast": "Timothee Chalamet, Zendaya, Rebecca Ferguson",
        "desc": "Paul Atreides unites with Chani and the Fremen while seeking revenge against those who destroyed his family.",
        "year": 2024, "duration": 166, "imdb": 8.5, "rating": "UA", "lang": "english",
        "categories": ["sci_fi", "action"],
        "poster": "https://image.tmdb.org/t/p/w500/1pdfLvkbY9ohJlCjQH2CZjjYVvJ.jpg",
        "trailer": "https://www.youtube.com/embed/Way9Dexny3w",
        "tags": "desert,spice,messiah,epic,politics", "featured": True,
    },
    {
        "title": "Top Gun: Maverick",
        "director": "Joseph Kosinski",
        "cast": "Tom Cruise, Miles Teller, Jennifer Connelly",
        "desc": "After thirty years of service as a top naval aviator, Pete Mitchell is pushing the envelope as a test pilot.",
        "year": 2022, "duration": 130, "imdb": 8.3, "rating": "UA", "lang": "english",
        "categories": ["action"],
        "poster": "https://image.tmdb.org/t/p/w500/62HCnUTHOIT6EzFEVu2hMnvKdGH.jpg",
        "trailer": "https://www.youtube.com/embed/giXco2jaZ_4",
        "tags": "jets,military,air-force,training,flying", "featured": True,
    },
    {
        "title": "KGF Chapter 2",
        "director": "Prashanth Neel",
        "cast": "Yash, Sanjay Dutt, Raveena Tandon",
        "desc": "Rocky's bloodlust for power spreads across the country as he faces his most dangerous enemies yet.",
        "year": 2022, "duration": 168, "imdb": 8.4, "rating": "A", "lang": "hindi",
        "categories": ["action"],
        "poster": "https://image.tmdb.org/t/p/w500/bQXAqRx2Fgc46uCVWgoPz5L5Dtr.jpg",
        "trailer": "https://www.youtube.com/embed/Kz8TJXoEXIQ",
        "tags": "gold,mines,revenge,empire,mass", "featured": True,
    },
    {
        "title": "RRR",
        "director": "S.S. Rajamouli",
        "cast": "N.T. Rama Rao Jr., Ram Charan, Alia Bhatt",
        "desc": "A fictitious story about two legendary revolutionaries and their journey away from home before they began the fight for their nation.",
        "year": 2022, "duration": 187, "imdb": 7.9, "rating": "UA", "lang": "telugu",
        "categories": ["action"],
        "poster": "https://image.tmdb.org/t/p/w500/nEufeZlyAOLqO2brDb3Z9tMIYxB.jpg",
        "trailer": "https://www.youtube.com/embed/NgNRBa_9Y8E",
        "tags": "revolution,friendship,british-raj,telugu,period", "featured": True,
    },
    {
        "title": "Pushpa: The Rise",
        "director": "Sukumar",
        "cast": "Allu Arjun, Fahadh Faasil, Rashmika Mandanna",
        "desc": "A laborer rises through the ranks of a red sandalwood smuggling syndicate.",
        "year": 2021, "duration": 179, "imdb": 7.6, "rating": "A", "lang": "telugu",
        "categories": ["action"],
        "poster": "https://image.tmdb.org/t/p/w500/r9oEXsGzM3HqXvFVjn8MVEkfDx4.jpg",
        "trailer": "https://www.youtube.com/embed/Q1NKMPhP8PY",
        "tags": "smuggling,jungle,red-sanders,mass,telugu",
    },
    {
        "title": "Vikram",
        "director": "Lokesh Kanagaraj",
        "cast": "Kamal Haasan, Vijay Sethupathi, Fahadh Faasil",
        "desc": "A black ops team hunts a serial killer who targets plainclothes police officers.",
        "year": 2022, "duration": 174, "imdb": 8.4, "rating": "A", "lang": "tamil",
        "categories": ["crime", "action"],
        "poster": "https://image.tmdb.org/t/p/w500/72HxCBdSWgS3IaJfO8nTGNkGlxb.jpg",
        "trailer": "https://www.youtube.com/embed/OKBMCL-frPU",
        "tags": "police,drugs,undercover,tamil,mass",
    },
    {
        "title": "3 Idiots",
        "director": "Rajkumar Hirani",
        "cast": "Aamir Khan, R. Madhavan, Sharman Joshi",
        "desc": "Two friends search for their long lost companion and revisit their college days.",
        "year": 2009, "duration": 170, "imdb": 8.4, "rating": "U", "lang": "hindi",
        "categories": ["comedy"],
        "poster": "https://image.tmdb.org/t/p/w500/66A9MqXOyVFCssoloscw79z8Tew.jpg",
        "trailer": "https://www.youtube.com/embed/K0eDlFX9GMc",
        "tags": "college,friendship,india,education,fun", "featured": True,
    },
    {
        "title": "Dangal",
        "director": "Nitesh Tiwari",
        "cast": "Aamir Khan, Fatima Sana Shaikh, Sanya Malhotra",
        "desc": "Former wrestler Mahavir Singh Phogat trains his daughters to become world-class wrestlers.",
        "year": 2016, "duration": 161, "imdb": 8.4, "rating": "U", "lang": "hindi",
        "categories": ["family"],
        "poster": "https://image.tmdb.org/t/p/w500/yjjet2M6Gq41C4s2b5xVNX8vLi9.jpg",
        "trailer": "https://www.youtube.com/embed/x_7YlGv9u1g",
        "tags": "wrestling,daughters,sports,india,inspirational",
    },
    {
        "title": "Andhadhun",
        "director": "Sriram Raghavan",
        "cast": "Ayushmann Khurrana, Tabu, Radhika Apte",
        "desc": "A series of dark misadventures befall a blind piano player after he witnesses a murder.",
        "year": 2018, "duration": 139, "imdb": 8.3, "rating": "UA", "lang": "hindi",
        "categories": ["crime"],
        "poster": "https://image.tmdb.org/t/p/w500/oXiHOAJt4sXOm66KXGQB1KnFiop.jpg",
        "trailer": "https://www.youtube.com/embed/jdCRWqQCKAM",
        "tags": "blind,music,murder,comedy,dark",
    },
]


# ── THEATRES ─────────────────────────────────────────────────────────────────
# CRITICAL: All Amalapuram theatre locations contain
# "East Godavari, Andhra Pradesh" so BOTH searches work:
#   → Search "Amalapuram"    ✔
#   → Search "East Godavari" ✔
# Same pattern for all other East Godavari district towns.

THEATRES_DATA = [
    # ── Amalapuram – MANDATORY 3 theatres ────────────────────────────────────
    {
        "name": "VPC 4K Dolby Atmos",
        "city": "Amalapuram",
        "location": "Clock Tower Center, Amalapuram, East Godavari, Andhra Pradesh",
        "screens": [
            {"name": "Screen 1", "rows": 9, "cols": 11},
            {"name": "Screen 2", "rows": 8, "cols": 10},
        ],
    },
    {
        "name": "Sekhar Cinemas",
        "city": "Amalapuram",
        "location": "Main Road, Amalapuram, East Godavari, Andhra Pradesh",
        "screens": [
            {"name": "Screen 1", "rows": 8, "cols": 10},
            {"name": "Screen 2", "rows": 7, "cols": 9},
        ],
    },
    {
        "name": "Sri Ganapathi Picture Palace",
        "city": "Amalapuram",
        "location": "Edarapalle, Amalapuram, East Godavari, Andhra Pradesh",
        "screens": [
            {"name": "Screen 1", "rows": 8, "cols": 9},
            {"name": "Screen 2", "rows": 7, "cols": 8},
        ],
    },
    # ── Rajahmundry ───────────────────────────────────────────────────────────
    {
        "name": "Geetha Apsara Theatre",
        "city": "Rajahmundry",
        "location": "Main Road, Rajahmundry, East Godavari, Andhra Pradesh",
        "screens": [
            {"name": "Screen 1", "rows": 10, "cols": 12},
            {"name": "Screen 2 (Premium)", "rows": 8, "cols": 10},
        ],
    },
    {
        "name": "Srinivasa Cinemas",
        "city": "Rajahmundry",
        "location": "T Nagar, Rajahmundry, East Godavari, Andhra Pradesh",
        "screens": [
            {"name": "Screen 1", "rows": 9, "cols": 11},
            {"name": "Screen 2", "rows": 8, "cols": 10},
        ],
    },
    {
        "name": "Sri Rama Theatre",
        "city": "Rajahmundry",
        "location": "Morampudi Junction, Rajahmundry, East Godavari, Andhra Pradesh",
        "screens": [
            {"name": "Screen 1", "rows": 10, "cols": 11},
            {"name": "Screen 2", "rows": 8, "cols": 9},
        ],
    },
    # ── Kakinada ──────────────────────────────────────────────────────────────
    {
        "name": "Swarna Theatre",
        "city": "Kakinada",
        "location": "Main Road, Kakinada, East Godavari, Andhra Pradesh",
        "screens": [
            {"name": "Screen 1", "rows": 9, "cols": 11},
            {"name": "Screen 2", "rows": 8, "cols": 10},
        ],
    },
    {
        "name": "Jagadamba Multiplex",
        "city": "Kakinada",
        "location": "Jagannaickpur, Kakinada, East Godavari, Andhra Pradesh",
        "screens": [
            {"name": "Screen 1", "rows": 8, "cols": 10},
            {"name": "Screen 2", "rows": 7, "cols": 9},
        ],
    },
    # ── Mandapeta ─────────────────────────────────────────────────────────────
    {
        "name": "Mandapeta Cine Complex",
        "city": "Mandapeta",
        "location": "Main Road, Mandapeta, East Godavari, Andhra Pradesh",
        "screens": [
            {"name": "Screen 1", "rows": 8, "cols": 9},
            {"name": "Screen 2", "rows": 7, "cols": 8},
        ],
    },
    # ── Ramachandrapuram ──────────────────────────────────────────────────────
    {
        "name": "Ramachandrapuram Theatre",
        "city": "Ramachandrapuram",
        "location": "Town Centre, Ramachandrapuram, East Godavari, Andhra Pradesh",
        "screens": [
            {"name": "Screen 1", "rows": 7, "cols": 9},
            {"name": "Screen 2", "rows": 6, "cols": 8},
        ],
    },
    # ── Ravulapalem ───────────────────────────────────────────────────────────
    {
        "name": "Ravulapalem Cinemas",
        "city": "Ravulapalem",
        "location": "Main Road, Ravulapalem, East Godavari, Andhra Pradesh",
        "screens": [
            {"name": "Screen 1", "rows": 7, "cols": 9},
            {"name": "Screen 2", "rows": 6, "cols": 8},
        ],
    },
    # ── Samalkot ──────────────────────────────────────────────────────────────
    {
        "name": "Samalkot Central Theatre",
        "city": "Samalkot",
        "location": "Town Centre, Samalkot, East Godavari, Andhra Pradesh",
        "screens": [
            {"name": "Screen 1", "rows": 8, "cols": 9},
            {"name": "Screen 2", "rows": 7, "cols": 8},
        ],
    },
    # ── Hyderabad ─────────────────────────────────────────────────────────────
    {
        "name": "PVR Cinemas Hyderabad",
        "city": "Hyderabad",
        "location": "GVK One Mall, Banjara Hills, Hyderabad, Telangana",
        "screens": [
            {"name": "Screen 1 (IMAX)", "rows": 12, "cols": 15},
            {"name": "Screen 2 (Premium)", "rows": 9, "cols": 11},
        ],
    },
    {
        "name": "AMB Cinemas",
        "city": "Hyderabad",
        "location": "Gachibowli, Hyderabad, Telangana",
        "screens": [
            {"name": "Screen 1", "rows": 10, "cols": 12},
            {"name": "Screen 2", "rows": 8, "cols": 10},
        ],
    },
    # ── Vijayawada ────────────────────────────────────────────────────────────
    {
        "name": "INOX Vijayawada",
        "city": "Vijayawada",
        "location": "Forum Sujana Mall, Benz Circle, Vijayawada, Andhra Pradesh",
        "screens": [
            {"name": "Screen 1", "rows": 10, "cols": 12},
            {"name": "Screen 2", "rows": 8, "cols": 10},
        ],
    },
    {
        "name": "Sri Raja Rajeshwari Cinemas",
        "city": "Vijayawada",
        "location": "Governorpet, Vijayawada, Andhra Pradesh",
        "screens": [
            {"name": "Screen 1", "rows": 9, "cols": 11},
            {"name": "Screen 2", "rows": 8, "cols": 9},
        ],
    },
]


FOOD_ITEMS_DATA = [
    {"name": "Classic Popcorn (Large)", "category": "snacks",  "price": 220, "desc": "Butter & salt popcorn in large bucket"},
    {"name": "Caramel Popcorn",         "category": "snacks",  "price": 250, "desc": "Sweet caramel coated popcorn"},
    {"name": "Nachos with Cheese",      "category": "snacks",  "price": 280, "desc": "Crispy nachos with warm cheese dip"},
    {"name": "Pepsi (Large)",           "category": "drinks",  "price": 130, "desc": "Chilled Pepsi in large cup"},
    {"name": "Coca-Cola (Large)",       "category": "drinks",  "price": 130, "desc": "Chilled Coca-Cola in large cup"},
    {"name": "Fresh Lime Soda",         "category": "drinks",  "price": 90,  "desc": "Sweet or salty fresh lime soda"},
    {"name": "Masala Chai",             "category": "drinks",  "price": 60,  "desc": "Hot spiced Indian tea"},
    {"name": "Combo: Popcorn + Pepsi",  "category": "combos",  "price": 320, "desc": "Large popcorn + large Pepsi combo"},
    {"name": "Combo: Nachos + Cold Drink", "category": "combos", "price": 360, "desc": "Nachos + any cold drink"},
    {"name": "Super Family Combo",      "category": "combos",  "price": 680, "desc": "2 Large popcorns + 2 drinks + nachos"},
    {"name": "Hot Dog",                 "category": "snacks",  "price": 160, "desc": "Classic hot dog with condiments"},
    {"name": "Samosa (2 pcs)",          "category": "snacks",  "price": 80,  "desc": "Crispy potato samosas"},
    {"name": "Choco Bar",               "category": "snacks",  "price": 100, "desc": "Rich chocolate ice cream bar"},
    {"name": "Water Bottle (500ml)",    "category": "drinks",  "price": 30,  "desc": "Chilled mineral water"},
    {"name": "Coffee (Hot/Cold)",       "category": "drinks",  "price": 120, "desc": "Freshly brewed coffee"},
]

COUPON_DATA = [
    {"code": "FIRST50",   "type": "flat",    "value": 50,  "min": 200, "max": 50,  "limit": 500},
    {"code": "SAVE20",    "type": "percent", "value": 20,  "min": 300, "max": 200, "limit": 200},
    {"code": "WEEKEND15", "type": "percent", "value": 15,  "min": 150, "max": 150, "limit": 300},
    {"code": "GOLD100",   "type": "flat",    "value": 100, "min": 500, "max": 100, "limit": 100},
    {"code": "NEWUSER",   "type": "percent", "value": 25,  "min": 100, "max": 250, "limit": 1000},
]


class Command(BaseCommand):
    help = "Seed the database with movies, theatres, shows, food items, coupons, and demo users"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("🎬 Starting CineAI seed..."))
        self._create_users()
        self._create_categories()
        self._create_movies()
        self._create_theatres_screens()
        self._create_shows()
        self._create_food()
        self._create_coupons()
        self._verify_amalapuram()
        self.stdout.write(self.style.SUCCESS("✅ Seed complete! CineAI is ready."))
        self.stdout.write(self.style.SUCCESS("   Admin : http://127.0.0.1:8000/admin-panel/"))
        self.stdout.write(self.style.SUCCESS("   Login : admin / admin123  |  demo / demo123"))

    # ── helpers ───────────────────────────────────────────────────────────────

    def _create_users(self):
        if not User.objects.filter(username="admin").exists():
            u = User.objects.create_superuser("admin", "admin@cinai.com", "admin123")
            u.first_name = "Admin"
            u.save()
            UserProfile.objects.get_or_create(user=u)
            self.stdout.write("  + admin created")
        else:
            self.stdout.write("  - admin exists, skip")

        if not User.objects.filter(username="demo").exists():
            u = User.objects.create_user("demo", "demo@cinai.com", "demo123")
            u.first_name = "Demo"
            u.save()
            UserProfile.objects.get_or_create(
                user=u,
                defaults={"phone": "9876543210", "city": "Amalapuram"},
            )
            self.stdout.write("  + demo created")
        else:
            self.stdout.write("  - demo exists, skip")

    def _create_categories(self):
        cats = [
            ("action",    "action",    "💥"),
            ("crime",     "crime",     "🔍"),
            ("family",    "family",    "👨‍👩‍👧"),
            ("horror",    "horror",    "👻"),
            ("comedy",    "comedy",    "😂"),
            ("drama",     "drama",     "🎭"),
            ("thriller",  "thriller",  "😰"),
            ("sci_fi",    "sci-fi",    "🚀"),
            ("romance",   "romance",   "❤️"),
            ("animation", "animation", "🎨"),
        ]
        for name, slug, icon in cats:
            Category.objects.get_or_create(slug=slug, defaults={"name": name, "icon": icon})
        self.stdout.write(f"  + {len(cats)} categories ready")

    def _create_movies(self):
        created = skipped = 0
        for data in MOVIES_DATA:
            slug = slugify(data["title"])
            if Movie.objects.filter(slug=slug).exists():
                skipped += 1
                continue
            movie = Movie.objects.create(
                title=data["title"],
                slug=slug,
                description=data["desc"],
                cast=data["cast"],
                director=data["director"],
                duration_minutes=data["duration"],
                release_date=date(data["year"], 6, 15),
                language=data["lang"],
                rating=data.get("rating", "UA"),
                imdb_score=data["imdb"],
                poster_url=data.get("poster", ""),
                trailer_url=data.get("trailer", ""),
                tags=data.get("tags", ""),
                is_featured=data.get("featured", False),
                is_active=True,
            )
            for cat_slug in data.get("categories", []):
                db_slug = "sci-fi" if cat_slug == "sci_fi" else cat_slug
                try:
                    movie.categories.add(Category.objects.get(slug=db_slug))
                except Category.DoesNotExist:
                    pass
            created += 1
        self.stdout.write(f"  + {created} movies created  ({skipped} already existed)")

    def _create_theatres_screens(self):
        t_new = s_new = 0
        for td in THEATRES_DATA:
            theatre, t_created = Theatre.objects.get_or_create(
                name=td["name"],
                city=td["city"],
                defaults={"location": td["location"]},
            )
            # Always sync location so East Godavari string is present
            if theatre.location != td["location"]:
                theatre.location = td["location"]
                theatre.save()
            if t_created:
                t_new += 1

            for sd in td["screens"]:
                _, sc = Screen.objects.get_or_create(
                    theatre=theatre,
                    name=sd["name"],
                    defaults={
                        "total_rows":    sd["rows"],
                        "seats_per_row": sd["cols"],
                    },
                )
                if sc:
                    s_new += 1
        self.stdout.write(f"  + {t_new} theatres, {s_new} screens created")

    def _create_shows(self):
        """
        3 days x 3 fixed timings x every screen.
        Movies assigned round-robin per screen – every screen gets a show.
        Amalapuram screens are listed FIRST in THEATRES_DATA so they are
        guaranteed to get shows from the first movies in the active list.
        """
        show_times = [time(10, 30), time(14, 0), time(18, 30)]
        prices     = [150, 180, 200]
        today      = timezone.now().date()

        movies  = list(Movie.objects.filter(is_active=True).order_by("id"))
        screens = list(Screen.objects.select_related("theatre").order_by("id"))

        if not movies:
            self.stdout.write(self.style.ERROR("  ! No active movies found"))
            return
        if not screens:
            self.stdout.write(self.style.ERROR("  ! No screens found"))
            return

        created = 0
        for idx, screen in enumerate(screens):
            movie = movies[idx % len(movies)]
            for day_offset in range(3):
                show_date = today + timedelta(days=day_offset)
                for show_time in show_times:
                    _, new = Show.objects.get_or_create(
                        movie=movie,
                        screen=screen,
                        show_date=show_date,
                        show_time=show_time,
                        defaults={"ticket_price": random.choice(prices)},
                    )
                    if new:
                        created += 1

        self.stdout.write(
            f"  + {created} shows created  "
            f"(3 days x {len(screens)} screens x 3 timings)"
        )

    def _create_food(self):
        created = 0
        for item in FOOD_ITEMS_DATA:
            _, new = FoodItem.objects.get_or_create(
                name=item["name"],
                defaults={
                    "category":     item["category"],
                    "price":        item["price"],
                    "description":  item["desc"],
                    "is_available": True,
                },
            )
            if new:
                created += 1
        self.stdout.write(f"  + {created} food items created")

    def _create_coupons(self):
        today = timezone.now().date()
        created = 0
        for c in COUPON_DATA:
            _, new = Coupon.objects.get_or_create(
                code=c["code"],
                defaults={
                    "discount_type":   c["type"],
                    "discount_value":  c["value"],
                    "min_order_value": c["min"],
                    "max_discount":    c["max"],
                    "usage_limit":     c["limit"],
                    "valid_from":      today,
                    "valid_to":        today + timedelta(days=90),
                    "is_active":       True,
                },
            )
            if new:
                created += 1
        self.stdout.write(f"  + {created} coupons created")

    def _verify_amalapuram(self):
        """Terminal sanity check – confirms Amalapuram theatres and shows exist."""
        self.stdout.write(self.style.WARNING("\n── Amalapuram Verification ──"))
        amal = Theatre.objects.filter(city="Amalapuram")
        for t in amal:
            shows = Show.objects.filter(screen__theatre=t).count()
            self.stdout.write(
                f"  ✔  {t.name}\n"
                f"     location : {t.location}\n"
                f"     shows    : {shows}"
            )
        if not amal.exists():
            self.stdout.write(self.style.ERROR("  ✘ No Amalapuram theatres found!"))