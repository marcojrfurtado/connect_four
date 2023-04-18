from django.db import models
import json
from game_app.exceptions import IllegalMoveException
from enum import Enum

ROW_COUNT = 7
COLUMN_COUNT = 7
WIN_COUNT = 4


class GameState(str, Enum):
    waiting_room = 'waiting_room'
    started = 'started'
    winner_found = 'winner'
    draw = 'draw'


class PlayerCharacter(str, Enum):
    player1 = 'O'
    player2 = 'X'


class BoardSide(str, Enum):
    left = 'L'
    right = 'R'


class Board:
    """
    Connect four two-dimensional board.
    """
    def __init__(self, board, move_count):
        """
        Default board constructor
        :param board: two-dimensional array representing the board (e.g. [['_', '_'], ['_', '_']])
        :param move_count: Counter of moves that have been performed by players on the input board.
        """
        self.rows = len(board)
        self.columns = len(board[0])
        self.max_moves = self.rows * self.columns
        self.board = board
        self.move_count = move_count

    @classmethod
    def clear_board(cls, rows=ROW_COUNT, columns=COLUMN_COUNT):
        """
        Creates a brand new two-dimensional clear board.
        :param rows: Number of rows in the board
        :param columns: Number of columns of the board.
        :return: two-dimensional clear board.
        """
        starting_board = [["_" for _ in range(columns)] for _ in range(rows)]
        return cls(starting_board, 0)

    @classmethod
    def from_json(cls, json_str):
        """
        Decodes board from a JSON string
        :param json_str: JSON string representing board.
        :return: Instance of board.
        """
        data = json.loads(json_str)
        return cls(data['board'], data['move_count'])

    def __iter__(self):
        for attr, value in self.__dict__.items():
            yield attr, value

    def move(self, row: int, side: str, char: PlayerCharacter):
        """
        Process a new player move. Throw exception if move is invalid. Update board if valid.
        :param row: Row where character will be placed.
        :param side: Side where character will be placed, either left of right.
        :param char: Character to be player, either X or O.
        """
        if self.move_count >= self.max_moves:
            raise IllegalMoveException('Reached the maximum number of movements.')

        if row < 0 or row >= self.rows:
            raise IllegalMoveException('Invalid row')

        if side != BoardSide.left and side != BoardSide.right:
            raise IllegalMoveException('Invalid side')

        if char != PlayerCharacter.player1 and char != PlayerCharacter.player2:
            raise IllegalMoveException('Invalid player character')

        try:
            if side == BoardSide.left:
                col = self.board[row].index('_')
            else:
                col = next(i for i in reversed(range(len(self.board[row]))) if self.board[row][i] == '_')
        except (ValueError, StopIteration):
            raise IllegalMoveException('Unable to place character in the specified row.')

        self.board[row][col] = char
        self.move_count += 1

    def find_winner(self):
        """
        Given the current state of the board, find out if there is a winner.
        :return: Character that won, either X or O. None if no winner found.
        """
        if self._is_winner(PlayerCharacter.player1):
            return PlayerCharacter.player1
        if self._is_winner(PlayerCharacter.player2):
            return PlayerCharacter.player2
        return None

    def _is_winner(self, character):
        count = 0
        # Horizontal check
        for row in self.board:
            for el in row:
                count = count + 1 if el == character else 0
                if count >= WIN_COUNT:
                    return True
            count = 0

        # Vertical check
        for col_ix in range(self.columns):
            for row_ix in range(self.rows):
                count = count + 1 if self.board[row_ix][col_ix] == character else 0
                if count >= WIN_COUNT:
                    return True
            count = 0

        # First Diagonal check (\)
        for row_ix in range(self.rows-WIN_COUNT+1):
            for col_ix in range(self.columns-WIN_COUNT+1):
                i, j = row_ix, col_ix
                count = 0
                while self.board[i][j] == character:
                    count += 1
                    if count >= WIN_COUNT:
                        return True
                    i, j = i + 1, j + 1

        # Second Diagonal check (/)
        for row_ix in range(self.rows-WIN_COUNT+1):
            for col_ix in range(WIN_COUNT-1, self.columns):
                i, j = row_ix, col_ix
                count = 0
                while self.board[i][j] == character:
                    count += 1
                    if count >= WIN_COUNT:
                        return True
                    i, j = i + 1, j - 1

        return False

    def is_it_full(self):
        """
        :return: True if no more moves are allowed in this board. False otherwise.
        """
        return self.move_count >= self.max_moves

    def to_dict(self):
        return dict(self)

    def __str__(self):
        return json.dumps(self, default=lambda o: o.to_dict(), indent=2)


# Create your models here.
class Game(models.Model):
    """
    Model that stores all information about a game, including players, board and state.
    """
    player1 = models.CharField(max_length=32, null=True)
    player2 = models.CharField(max_length=32, null=True)
    board = models.TextField(default=str(Board.clear_board()))
    board_move_counter = models.IntegerField(default=0)
    winner = models.IntegerField(null=True, blank=True)
    state = models.CharField(max_length=32, default=GameState.waiting_room)

    def get_board(self):
        """
        :return: Get Board instance.
        """
        return Board.from_json(self.board)

    def get_current_turn(self):
        """
        :return: 1, if it is player 1's turn, 2 otherwise.
        """
        return 1 + (self.board_move_counter % 2)

    def update_board(self, board):
        """
        Update board.
        :param board: New board state.
        """
        self.board_move_counter = board.move_count
        self.board = str(board)

        winner_character = board.find_winner()
        if winner_character == PlayerCharacter.player1:
            self.winner = 1
        elif winner_character == PlayerCharacter.player2:
            self.winner = 2

        if self.winner is not None:
            self.state = GameState.winner_found
        elif board.is_it_full():
            self.state = GameState.draw

    def is_game_empty(self):
        return self.player1 is None and self.player2 is None

    def is_game_full(self):
        return self.player1 is not None and self.player2 is not None

    def join_game(self, player):
        """
        Tries to add a new player to this game. If both players joined, will move game to a started state.
        :param player: player, represented by a session id.
        :return: 1, if we added it as player 1. 2 if added as player 2. -1 if game is already full.
        """
        if self.is_game_full():
            return -1

        player_count = None
        if self.player1 is None:
            self.player1 = player
            player_count = 1
        elif self.player2 is None:
            self.player2 = player
            player_count = 2
        if self.is_game_full() and self.state == GameState.waiting_room:
            self.state = GameState.started
        return player_count

    def drop_from_game(self, player):
        """
        Drops player from game. If player is dropped, might move game back to waiting room.
        :param player: player, as represented by session id.
        """
        if player == self.player1:
            self.player1 = None
        elif player == self.player2:
            self.player2 = None
        else:
            return

        if self.state == GameState.started:
            self.state = GameState.waiting_room
