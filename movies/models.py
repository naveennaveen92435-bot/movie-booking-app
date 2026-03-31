"""
Movies App - Models
Defines: Category, Movie, Theatre, Screen, Show
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Category(models.Model):
    """Movie genre/category"""
    CATEGORY_CHOICES = [
        ('action', 'Action'),
        ('crime', 'Crime'),
        ('family', 'Family'),
        ('horror', 'Horror'),
        ('comedy', 'Comedy'),
        ('drama', 'Drama'),
        ('thriller', 'Thriller'),
        ('sci_fi', 'Sci-Fi'),
        ('romance', 'Romance'),
        ('animation', 'Animation'),
    ]
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, default='🎬')  # emoji icon

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()


class Movie(models.Model):
    """Core movie model"""
    LANGUAGE_CHOICES = [
        ('english', 'English'),
        ('hindi', 'Hindi'),
        ('telugu', 'Telugu'),
        ('tamil', 'Tamil'),
        ('malayalam', 'Malayalam'),
    ]
    RATING_CHOICES = [
        ('U', 'U - Universal'),
        ('UA', 'UA - Universal Adult'),
        ('A', 'A - Adult'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    cast = models.TextField(help_text='Comma-separated cast names')
    director = models.CharField(max_length=100)
    duration_minutes = models.PositiveIntegerField()
    release_date = models.DateField()
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='english')
    rating = models.CharField(max_length=5, choices=RATING_CHOICES, default='UA')
    imdb_score = models.DecimalField(max_digits=3, decimal_places=1, default=7.0)
    poster = models.ImageField(upload_to='posters/', blank=True, null=True)
    poster_url = models.URLField(blank=True, help_text='External poster URL if no upload')
    trailer_url = models.URLField(blank=True, help_text='YouTube embed URL')
    categories = models.ManyToManyField(Category, related_name='movies')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # AI recommendation tags (comma-separated keywords)
    tags = models.CharField(max_length=500, blank=True,
                            help_text='Keywords for AI recommendations')

    class Meta:
        ordering = ['-release_date']

    def __str__(self):
        return self.title

    def get_poster_url(self):
        if self.poster_url:
            return self.poster_url
        if self.poster:
            return self.poster.url
        return '/static/images/default_poster.jpg'
    def get_cast_list(self):
        return [c.strip() for c in self.cast.split(',') if c.strip()]

    def get_tags_list(self):
        return [t.strip().lower() for t in self.tags.split(',') if t.strip()]

    @property
    def duration_display(self):
        hours = self.duration_minutes // 60
        mins = self.duration_minutes % 60
        return f"{hours}h {mins}m"


class Theatre(models.Model):
    """Theatre/Cinema hall"""
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=300)
    city = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.city}"


class Screen(models.Model):
    """Screen inside a theatre"""
    theatre = models.ForeignKey(Theatre, on_delete=models.CASCADE, related_name='screens')
    name = models.CharField(max_length=50)  # e.g., "Screen 1"
    total_rows = models.PositiveIntegerField(default=8)
    seats_per_row = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.theatre.name} - {self.name}"

    @property
    def total_seats(self):
        return self.total_rows * self.seats_per_row


class Show(models.Model):
    """A movie showing at a specific screen and time"""
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='shows')
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, related_name='shows')
    show_date = models.DateField()
    show_time = models.TimeField()
    ticket_price = models.DecimalField(max_digits=8, decimal_places=2, default=200.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['show_date', 'show_time']
        unique_together = ['screen', 'show_date', 'show_time']

    def __str__(self):
        return f"{self.movie.title} | {self.screen} | {self.show_date} {self.show_time}"

    def available_seats_count(self):
        booked = self.seat_bookings.filter(
            status__in=['confirmed', 'hold']
        ).count()
        return self.screen.total_seats - booked

    def occupancy_percentage(self):
        total = self.screen.total_seats
        if total == 0:
            return 0
        booked = self.seat_bookings.filter(status='confirmed').count()
        return round((booked / total) * 100, 1)