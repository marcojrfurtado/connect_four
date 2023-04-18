# game_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('game/<int:game_id>/', views.game, name='game'),
]