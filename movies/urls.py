"""Movies app URL patterns"""

from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('movie/<slug:slug>/', views.movie_detail, name='movie_detail'),

    # AJAX APIs
    path('api/search/', views.movie_search_api, name='search_api'),
    path('api/heatmap/<int:show_id>/', views.seat_heatmap_api, name='heatmap_api'),
    path('api/movies-by-city/', views.movies_by_city_api, name='movies_by_city_api'),
]