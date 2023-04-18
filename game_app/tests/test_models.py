from django.test import TestCase
from game_app.models import Board, PlayerCharacter, BoardSide
from game_app.exceptions import IllegalMoveException


class BoardTests(TestCase):

    def test_create_empty_board(self):
        b = Board.clear_board(20, 20)
        self.assertEquals(len(b.board), 20)
        for row in b.board:
            self.assertEquals(len(row), 20)
            self.assertTrue(all(x == '_' for x in row))
        self.assertEquals(b.max_moves, 400)
        self.assertEquals(b.move_count, 0)

    def test_load_predefined_board(self):
        board_json = '''
        {
            "rows": 7,
            "columns": 7,
            "max_moves": 49,
            "board": [
                ["_", "_", "_", "_", "_", "_", "_"],
                ["_", "_", "_", "_", "_", "_", "_"],
                ["X", "_", "_", "_", "_", "_", "_"],
                ["O", "O", "_", "_", "_", "_", "_"],
                ["_", "_", "_", "_", "_", "_", "_"],
                ["_", "_", "_", "_", "_", "X", "O"],
                ["_", "_", "_", "_", "_", "_", "_"]
            ],
        "move_count": 0
        }'''
        b = Board.from_json(board_json)
        self.assertEquals(len(b.board), 7)
        self.assertEquals(b.board[0], ['_'] * 7)
        self.assertEquals(b.board[1], ['_'] * 7)
        self.assertEquals(b.board[2], ['X'] + ['_'] * 6)
        self.assertEquals(b.board[3], ['O'] * 2 + ['_'] * 5)
        self.assertEquals(b.board[4], ['_'] * 7)
        self.assertEquals(b.board[5], ['_'] * 5 + ['X', 'O'])
        self.assertEquals(b.board[6], ['_'] * 7)
        self.assertEquals((b.rows, b.columns, b.move_count, b.max_moves), (7, 7, 0, 49))

    def test_winner_horizontal(self):
        board_json = '''
        {
            "rows": 7,
            "columns": 7,
            "max_moves": 49,
            "board": [
                ["X", "X", "X", "X", "_", "_", "_"],
                ["O", "_", "_", "_", "_", "_", "O"],
                ["_", "_", "_", "_", "_", "_", "_"],
                ["_", "_", "_", "_", "_", "_", "_"],
                ["_", "_", "_", "_", "_", "_", "_"],
                ["_", "_", "_", "_", "_", "_", "_"],
                ["O", "_", "_", "_", "_", "_", "O"]
            ],
            "move_count": 8
        }'''
        b = Board.from_json(board_json)
        self.assertEquals(b.find_winner(), PlayerCharacter.player2)

    def test_winner_vertical(self):
        board_json = '''
        {
            "rows": 7,
            "columns": 7,
            "max_moves": 49,
            "board": [
                ["X", "X", "_", "_", "_", "_", "_"],
                ["_", "_", "_", "_", "_", "_", "X"],
                ["_", "_", "_", "_", "_", "_", "_"],
                ["O", "_", "_", "_", "_", "_", "_"],
                ["O", "_", "_", "_", "_", "_", "_"],
                ["O", "_", "_", "_", "_", "_", "_"],
                ["O", "_", "_", "_", "_", "_", "X"]
            ],
            "move_count": 8
        }'''
        b = Board.from_json(board_json)
        self.assertEquals(b.find_winner(), PlayerCharacter.player1)


    def test_winner_diagonal_left_to_right(self):
        board_json = '''
        {
            "rows": 7,
            "columns": 7,
            "max_moves": 49,
            "board": [
                ["X", "_", "_", "_", "_", "_", "_"],
                ["_", "_", "_", "_", "_", "_", "_"],
                ["_", "_", "_", "_", "_", "_", "_"],
                ["O", "_", "_", "_", "_", "_", "_"],
                ["O", "O", "_", "_", "_", "_", "_"],
                ["O", "X", "O", "_", "_", "_", "_"],
                ["X", "X", "X", "O", "_", "_", "_"]
            ],
            "move_count": 11
        }'''
        b = Board.from_json(board_json)
        self.assertEquals(b.find_winner(), PlayerCharacter.player1)

    def test_winner_diagonal_right_to_left(self):
        board_json = '''
        {
            "rows": 7,
            "columns": 7,
            "max_moves": 49,
            "board": [
                ["X", "_", "_", "_", "_", "_", "_"],
                ["_", "_", "_", "_", "_", "_", "_"],
                ["_", "_", "_", "_", "_", "_", "_"],
                ["_", "_", "_", "_", "_", "_", "O"],
                ["_", "_", "_", "_", "_", "O", "O"],
                ["_", "_", "_", "_", "O", "X", "O"],
                ["_", "_", "_", "O", "X", "X", "X"]
            ],
            "move_count": 11
        }'''
        b = Board.from_json(board_json)
        self.assertEquals(b.find_winner(), PlayerCharacter.player1)

    def test_draw_complete(self):
        board_json = '''
        {
            "rows": 7,
            "columns": 7,
            "max_moves": 49,
            "board": [
                ["X", "X", "O", "O", "X", "X", "O"],
                ["O", "O", "X", "X", "O", "O", "X"],
                ["X", "X", "O", "O", "X", "X", "O"],
                ["O", "O", "X", "X", "O", "O", "X"],
                ["X", "X", "O", "O", "X", "X", "O"],
                ["O", "O", "X", "X", "O", "O", "X"],
                ["X", "X", "O", "O", "X", "X", "O"]
            ],
        "move_count": 49
        }'''
        b = Board.from_json(board_json)
        self.assertEquals(b.find_winner(), None)
        self.assertTrue(b.is_it_full())

    def test_move_valid(self):
        board_json = '''
        {
            "rows": 7,
            "columns": 7,
            "max_moves": 49,
            "board": [
                ["_", "_", "_", "_", "_", "_", "_"],
                ["_", "_", "_", "_", "_", "_", "_"],
                ["X", "_", "_", "_", "_", "_", "_"],
                ["O", "O", "_", "_", "_", "_", "_"],
                ["_", "_", "_", "_", "_", "_", "_"],
                ["_", "_", "_", "_", "_", "X", "O"],
                ["_", "_", "_", "_", "_", "_", "_"]
            ],
        "move_count": 5
        }'''
        b = Board.from_json(board_json)
        b.move(2, BoardSide.left, PlayerCharacter.player2)
        self.assertEquals(b.board[2][1], PlayerCharacter.player2)

    def test_move_invalid_row_full(self):
        board_json = '''
            {
                "rows": 7,
                "columns": 7,
                "max_moves": 49,
                "board": [
                    ["X", "O", "X", "O", "X", "O", "X"],
                    ["_", "_", "_", "_", "_", "_", "_"],
                    ["_", "_", "_", "_", "_", "_", "_"],
                    ["_", "_", "_", "_", "_", "_", "_"],
                    ["_", "_", "_", "_", "_", "_", "_"],
                    ["_", "_", "_", "_", "_", "_", "_"],
                    ["_", "_", "_", "_", "_", "_", "_"]
                ],
            "move_count": 7
            }'''
        b = Board.from_json(board_json)
        with self.assertRaises(IllegalMoveException):
            b.move(0, BoardSide.left, PlayerCharacter.player1)
        with self.assertRaises(IllegalMoveException):
            b.move(0, BoardSide.right, PlayerCharacter.player1)

    def test_move_invalid_out_of_bounds(self):
        board_json = '''
            {
                "rows": 7,
                "columns": 7,
                "max_moves": 49,
                "board": [
                    ["X", "O", "X", "O", "_", "_", "_"],
                    ["_", "_", "_", "_", "_", "_", "_"],
                    ["_", "_", "_", "_", "_", "_", "_"],
                    ["_", "_", "_", "_", "_", "_", "_"],
                    ["_", "_", "_", "_", "_", "_", "_"],
                    ["_", "_", "_", "_", "_", "_", "_"],
                    ["_", "_", "_", "_", "_", "_", "_"]
                ],
            "move_count": 4
            }'''
        b = Board.from_json(board_json)
        with self.assertRaises(IllegalMoveException):
            b.move(10, BoardSide.left, PlayerCharacter.player1)




