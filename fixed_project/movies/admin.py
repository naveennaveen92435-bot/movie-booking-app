from django.contrib import admin
from .models import Category, Movie, Theatre, Screen, Show


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'language', 'rating', 'imdb_score', 'release_date', 'is_active', 'is_featured']
    list_filter = ['categories', 'language', 'rating', 'is_active', 'is_featured']
    search_fields = ['title', 'cast', 'director']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['categories']
    list_editable = ['is_active', 'is_featured']
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'slug', 'description', 'categories')
        }),
        ('Movie Details', {
            'fields': ('cast', 'director', 'duration_minutes', 'release_date', 'language', 'rating', 'imdb_score')
        }),
        ('Media', {
            'fields': ('poster', 'poster_url', 'trailer_url')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_featured', 'tags')
        }),
    )


@admin.register(Theatre)
class TheatreAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'location', 'is_active']
    list_filter = ['city', 'is_active']
    search_fields = ['name', 'city', 'location']
    list_editable = ['is_active']


@admin.register(Screen)
class ScreenAdmin(admin.ModelAdmin):
    list_display = ['name', 'theatre', 'total_rows', 'seats_per_row', 'total_seats', 'is_active']
    list_filter = ['theatre', 'is_active']
    search_fields = ['name', 'theatre__name']
    list_editable = ['is_active']


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ['movie', 'screen', 'show_date', 'show_time', 'ticket_price', 'is_active']
    list_filter = ['show_date', 'movie', 'screen__theatre', 'is_active']
    search_fields = ['movie__title', 'screen__name']
    list_editable = ['ticket_price', 'is_active']
    date_hierarchy = 'show_date'