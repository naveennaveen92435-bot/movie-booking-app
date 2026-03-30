"""
Accounts App - Models
Extended user profile model
"""

from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Extended profile for registered users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True)
    avatar_url = models.URLField(blank=True)
    dark_mode = models.BooleanField(default=False)
    preferred_genres = models.CharField(max_length=300, blank=True,
                                        help_text='Comma-separated genre slugs')
    city = models.CharField(max_length=100, blank=True)
    is_blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile: {self.user.username}"

    def get_preferred_genres_list(self):
        return [g.strip() for g in self.preferred_genres.split(',') if g.strip()]
