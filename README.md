# 🎬 Smart AI Movie Booking System — CinéAI

A production-style full-stack movie ticket booking system built with **Django** (backend), **HTML/CSS/JS** (frontend), and **SQLite** (database). Features AI movie recommendations, smart seat suggestions, QR code tickets, and a complete admin dashboard.

---

## ✨ Features

### User Features
- 🎬 **Homepage** — Movie grid, hero slider, category filters, live search
- 🤖 **AI Recommendations** — Content-based + collaborative filtering engine
- 🎞️ **Movie Detail** — Embedded trailer, cast info, show timings by date
- 💺 **Seat Selection** — Live seat layout, hold timer (10min), AI seat suggestions, heatmap
- 🍿 **Food Pre-booking** — Add snacks/drinks with quantity controls
- 💳 **Payment** — UPI / Card / Cash with coupon support
- 🎫 **QR Ticket** — Downloadable ticket with QR code entry system
- 👤 **Profile** — My bookings, history, cancel/rebook, notifications
- 🎙️ **Voice Booking** — Web Speech API integration
- 🌙 **Dark Mode** — Persistent per-user preference
- 🔄 **Auto Refund** — Tiered refund policy (100% / 75% / 50%)

### Admin Features
- 📊 **Dashboard** — Revenue, booking, user KPIs with Chart.js charts
- 🎬 **Movie Management** — Add/Edit/Delete movies with poster upload and trailer URL
- 🏢 **Theatre & Screen Management** — Multi-theatre, multi-screen with seat layout
- 📅 **Show Scheduling** — Calendar-based show management with occupancy tracking
- 📋 **Booking Management** — View, cancel, refund bookings
- 👥 **User Management** — View users, block/unblock
- 🍕 **Food & Coupons** — Manage menu items and discount codes
- 📈 **Reports** — Monthly revenue charts, top movies, genre popularity

---

## 🗂️ Project Structure

```
smart_movie_booking/
├── manage.py
├── settings.py
├── urls.py
├── wsgi.py
├── requirements.txt
├── setup.sh
│
├── movies/                     # Movies, Categories, Theatres, Screens, Shows
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── management/commands/
│       └── seed_data.py        # Seeds 60+ movies, theatres, shows
│
├── bookings/                   # Seat booking, payment, QR, food
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── ai_recommender.py       # AI recommendation + smart seat logic
│
├── accounts/                   # Auth, profiles, dark mode, notifications
│   ├── models.py
│   ├── views.py
│   └── urls.py
│
├── admin_panel/                # Custom admin dashboard
│   ├── views.py
│   └── urls.py
│
├── templates/
│   ├── base.html               # Navbar, footer, voice modal
│   ├── movies/
│   │   ├── homepage.html
│   │   └── movie_detail.html
│   ├── bookings/
│   │   ├── seat_selection.html
│   │   ├── payment.html
│   │   └── ticket_confirmation.html
│   ├── accounts/
│   │   ├── login.html
│   │   ├── register.html
│   │   └── profile.html
│   ├── admin_panel/
│   │   ├── base_admin.html
│   │   ├── dashboard.html
│   │   ├── movie_list.html
│   │   ├── movie_form.html
│   │   ├── theatre_list.html
│   │   ├── show_list.html
│   │   ├── booking_list.html
│   │   ├── user_list.html
│   │   ├── food_list.html
│   │   └── reports.html
│   └── partials/
│       └── movie_card.html
│
├── static/
│   ├── css/main.css            # Full cinematic dark theme
│   └── js/main.js              # Search, dark mode, voice, hero slider
│
└── media/                      # Uploaded posters, QR codes
```

---

## 🚀 Setup Instructions

### Prerequisites
- Python 3.9+
- pip

### Option A: Automated (Recommended)

```bash
cd smart_movie_booking
chmod +x setup.sh
./setup.sh
source venv/bin/activate
python manage.py runserver
```

### Option B: Manual Steps

```bash
# 1. Navigate to project
cd smart_movie_booking

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate          # Linux/Mac
# OR: venv\Scripts\activate       # Windows

# 3. Install dependencies
cd smart_movie_booking

# 4. Create database migrations
python manage.py makemigrations movies
python manage.py makemigrations bookings
python manage.py makemigrations accounts
python manage.py makemigrations admin_panel

# 5. Apply migrations
python manage.py migrate

# 6. Create media directories
mkdir -p media/posters media/trailers media/qr_codes

# 7. Seed database (60+ movies, theatres, shows, food, coupons)
python manage.py seed_data

# 8. Run the server
python manage.py runserver
```

---

## 🌐 Access URLs

| URL | Description |
|-----|-------------|
| `http://127.0.0.1:8000/` | Homepage (movie listing) |
| `http://127.0.0.1:8000/accounts/login/` | User login |
| `http://127.0.0.1:8000/accounts/register/` | User registration |
| `http://127.0.0.1:8000/accounts/profile/` | User profile |
| `http://127.0.0.1:8000/admin-panel/` | Custom admin dashboard |
| `http://127.0.0.1:8000/django-admin/` | Django built-in admin |

---

## 🔐 Demo Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| User | `demo` | `demo123` |

---

## 🎬 Booking Flow

```
1. Browse Homepage  →  Filter by Genre / Search
2. Click Movie  →  View Detail + Trailer
3. Select Show Time  →  Seat Selection page
4. Choose Seats  →  AI suggests best seats
     • Seat hold timer (10 min auto-release)
     • Live heatmap refreshes every 15s
5. Add Food (optional)
6. Proceed to Payment  →  UPI / Card / Cash
     • Apply coupon codes
     • See refund policy
7. Confirm Booking  →  QR Ticket generated
8. Download Ticket  →  Scan at entrance
```

---

## 🤖 AI Features

### Movie Recommendations
Located in `bookings/ai_recommender.py`:
- Analyzes user's confirmed booking history
- Extracts genre signals weighted by frequency
- Applies 2x weight to profile-preferred genres
- Scores all unwatched movies by genre match + IMDb score + featured flag
- Returns top-N ranked movies

### Smart Seat Suggestion
- `suggest_seats(show, num_seats, preference)` 
- Preferences: `center`, `front`, `back`, `aisle`
- Finds best consecutive seats in the same row
- Falls back to individual best seats if no consecutive available

---

## 🗄️ Database Models

| App | Models |
|-----|--------|
| `movies` | `Category`, `Movie`, `Theatre`, `Screen`, `Show` |
| `bookings` | `SeatBooking`, `Booking`, `FoodItem`, `FoodOrder`, `Coupon`, `Notification` |
| `accounts` | `UserProfile` |

---

## 💡 Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 4.2 |
| Database | SQLite (default) / PostgreSQL ready |
| Frontend | Bootstrap 5 + Vanilla JS |
| Charts | Chart.js 4 |
| QR Code | `qrcode[pil]` |
| Fonts | Bebas Neue + DM Sans (Google Fonts) |
| Auth | Django built-in auth |
| Media | Pillow |

---

## 🔧 Configuration

Edit `settings.py` for:

```python
# Switch to PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'cineai_db',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Seat hold duration (minutes)
SEAT_HOLD_MINUTES = 10

# Production settings
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']
SECRET_KEY = 'your-secure-secret-key'
```

---

## 📦 Seed Data Summary

The `seed_data` command creates:
- **60+ movies** across 8 genres (Action, Crime, Horror, Comedy, Family, Thriller, Sci-Fi, Animation)
- **3 theatres** with **7 screens** in Hyderabad
- **Shows** for every active movie over the next 7 days (4-5 shows/day)
- **15 food items** (snacks, drinks, combos)
- **5 coupon codes** (FIRST50, SAVE20, WEEKEND15, GOLD100, NEWUSER)
- **2 demo users** (admin + demo)

---

## 🎨 UI Design

- **Cinematic dark theme** with gold accents (`#f5c518`)
- **Fonts**: Bebas Neue (display) + DM Sans (body) + DM Mono (data)
- **CSS Variables** for seamless dark/light mode switching
- Smooth hover animations on all interactive elements
- Responsive mobile layout

---

*Built with ❤️ as part of Smart AI Movie Booking System*
