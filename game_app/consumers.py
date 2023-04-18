# game_app/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

# game_app/consumers.py
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from enum import IntEnum
import json
from .models import Game, GameState, PlayerCharacter
from game_app.exceptions import IllegalMoveException


class WebsocketErrorCodes(IntEnum):
    unable_to_join = 4000


class GameConsumer(AsyncWebsocketConsumer):
    """
    Game controller. Consumers incoming player connections, coordinates player moves and broadcasts game state and errors.
    """
    game = None
    game_group_name = None
    game_id = None
    player_id = None
    player_count = None
    player_character = None

    async def connect(self):
        """
        Called anytime we accept a new incoming connections. Will attempt to connect player to the requested game.
        """
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.game_group_name = f'game_{self.game_id}'

        # Ensure that the current session has a session ID
        if not self.scope['session'].session_key:
            await database_sync_to_async(self.scope['session'].save)()

        self.player_id = self.scope['session'].session_key

        if self.game is None:
            await self._refresh_game()

        await self.accept()
        await self.channel_layer.group_add(self.game_group_name, self.channel_name)

        # If the current session is one of the players, accept the WebSocket connection
        if await self._join_game():
            await self.channel_layer.group_send(self.game_group_name, {'type': 'send_state'})
        else:
            await self.close(code=int(WebsocketErrorCodes.unable_to_join))

    async def disconnect(self, close_code):
        """
        Called anytime websocket connection is disconnected. Might result in removing player from game. If game is
        empty, game itself may be freed up.
        :param close_code: Code representing disconnect reason.
        :return:
        """
        await self.channel_layer.group_discard(
            self.game_group_name,
            self.channel_name
        )
        if close_code != int(WebsocketErrorCodes.unable_to_join):
            await self._drop_from_game()
            await self.channel_layer.group_send(self.game_group_name, {'type': 'send_state'})

    async def receive(self, text_data):
        """
        Processes move requests from players, and broadcast game state changes back to players.
        :param text_data: Player move, JSON-encoded.
        """
        try:
            text_data_json = json.loads(text_data)
            move = text_data_json['move']
            row, side = int(move[0]), move[1]

            await self._refresh_game()

            if not(self.game.state == GameState.started):
                raise IllegalMoveException('Game has not yet begun.')

            if not(self.game.get_current_turn() == self.player_count):
                raise IllegalMoveException('Please wait for your turn.')

            board = self.game.get_board()
            board.move(row, side, self.player_character)
            self.game.update_board(board)
            await self._save_game()
            await self.channel_layer.group_send(self.game_group_name, {'type': 'send_state'})
        except IllegalMoveException as e:
            await self._send_error(str(e))

    async def send_state(self, event=None):
        """
        Send latest game state.
        """
        await self._refresh_game()
        await self.send(json.dumps({
            'type': 'game_state',
            'state': self.game.state,
            'board': self.game.board,
            'player_room_id': self.player_count,
            'winner_room_id': self.game.winner,
            'turn_room_id': self.game.get_current_turn()
        }))

    @database_sync_to_async
    def _refresh_game(self):
        self.game, _ = Game.objects.get_or_create(pk=self.game_id)

    @database_sync_to_async
    def _join_game(self):
        if self.game.state != GameState.waiting_room:
            return False
        self.player_count = self.game.join_game(self.player_id)
        if self.player_count < 0:
            return False
        self.player_character = PlayerCharacter.player1 \
            if self.game.player1 == self.player_id else PlayerCharacter.player2
        self.game.save()
        return True

    @database_sync_to_async
    def _drop_from_game(self):
        self.game.drop_from_game(self.player_id)
        if self.game.is_game_empty():
            print('Deleting game room')
            self.game.delete()
        else:
            self.game.save()

    @database_sync_to_async
    def _save_game(self):
        self.game.save()

    async def _send_error(self, message):
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))