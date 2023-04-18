# Connect Four

## Requirements
* Python 3
* Django

### Setup instructions
```bash
pip install -r requirements.txt
python manage.py migrate
```

## Running the Server
```bash
daphne connect_four_project.asgi:application    
```

## Playing the game

1. First player opens the browser at http://12.0.0.1/game/<room_id>,
where *room_id* is a number representing the room number (e.g. http://127.0.0.1/game/22/).
Player will receive a message stating they are waiting for the opponent.
2. Second player joins the room with the same link, and game starts.

Note: After game room is created, if both players drop from the game, room
is freed.

## Documentation

Game is implemented with the help of Django Channels, which can easily
handle WebSocket communication for us. This allows us to easily handle incoming connections and broadcast
the state of the game to all players at every turn. Here is where the core of the implementation resides:

* *game_app/consumers.py*: This file contains the controller layer of
our application. It uses a websocket consumer that will accept connections of
incoming players, decide if they can join the game and coordinate messages 
to be sent back to them (e.g. game state or errors).
* *game_app/templates/game_app/game.html*: This is the frontend interface. For simplicity
there is no waiting room page, so users go directly to this page that displays the game.
* *game_app/models.py*: This file contains the game model, which is store
in SQLite. There is only one table used to persist the game state. This table contains the following attributes:
  * player1, player2: player ids, store as session keys;
  * board_move_counter: count moves player, used to define player turn;
  * board: JSON encoded board, updated at every turn;
  * state: game state;
  * winner: player who won, if known;
* *game_app/tests/test_models.py*: Only set of tests that have been included,
up to this point. Tests board update logic, including finding its winner.