#!/bin/bash
# ============================================================
# CinéAI — Smart Movie Booking System — Setup Script
# ============================================================

set -e

echo ""
echo "🎬  CinéAI — Smart AI Movie Booking System"
echo "============================================"

# 1. Create virtual environment
echo ""
echo "📦  Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
echo "📦  Installing dependencies..."
pip install -r requirements.txt

# 3. Make migrations
echo ""
echo "🗄️   Creating database migrations..."
python manage.py makemigrations movies
python manage.py makemigrations bookings
python manage.py makemigrations accounts
python manage.py makemigrations admin_panel

# 4. Apply migrations
echo "🗄️   Applying migrations..."
python manage.py migrate

# 5. Collect static (optional for dev)
echo ""
echo "📁  Creating media and static dirs..."
mkdir -p media/posters media/trailers media/qr_codes static/images

# 6. Create a default poster placeholder
python3 -c "
from PIL import Image, ImageDraw
img = Image.new('RGB', (300, 450), color='#1a1a26')
d = ImageDraw.Draw(img)
d.rectangle([10,10,290,440], outline='#f5c518', width=2)
d.text((150, 225), '🎬', fill='#f5c518', anchor='mm')
img.save('static/images/default_poster.jpg')
print('  ✓ Default poster created')
" 2>/dev/null || echo "  ⚠ Skipped placeholder (Pillow issue, not critical)"

# 7. Seed database
echo ""
echo "🌱  Seeding database with movies, theatres, shows..."
python manage.py seed_data

echo ""
echo "✅  Setup complete!"
echo ""
echo "╔════════════════════════════════════════╗"
echo "║         LAUNCH THE SERVER              ║"
echo "╠════════════════════════════════════════╣"
echo "║  source venv/bin/activate              ║"
echo "║  python manage.py runserver            ║"
echo "╠════════════════════════════════════════╣"
echo "║  Site:    http://127.0.0.1:8000/       ║"
echo "║  Admin:   http://127.0.0.1:8000/       ║"
echo "║           admin-panel/                 ║"
echo "╠════════════════════════════════════════╣"
echo "║  User login:   demo  / demo123         ║"
echo "║  Admin login:  admin / admin123        ║"
echo "╚════════════════════════════════════════╝"
echo ""
