from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

def game(request, game_id):
    return render(request, 'game_app/game.html', {'game_id': game_id})
