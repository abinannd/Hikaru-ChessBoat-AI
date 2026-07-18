import sys
import unittest
from pathlib import Path

import chess

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.move_encoder import (
    PROMOTION_OFFSET,
    PROMOTION_PAIR_COUNT,
    PROMOTION_PIECE_TYPES,
    TOTAL_CLASSES,
    decode_move,
    encode_move,
)


class MoveEncoderTests(unittest.TestCase):
    def assert_round_trip(self, uci, board):
        move = chess.Move.from_uci(uci)
        encoded = encode_move(move)
        decoded = decode_move(encoded, board)
        self.assertEqual(decoded.uci(), uci)
        self.assertEqual(decoded, move)

    def test_normal_moves_use_the_original_4096_class_space(self):
        boards = {
            "e2e4": chess.Board(),
            "g1f3": chess.Board(),
            "e7e5": chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"),
            "b8c6": chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"),
        }
        for uci in ["e2e4", "g1f3", "e7e5", "b8c6"]:
            with self.subTest(uci=uci):
                self.assert_round_trip(uci, boards[uci])

    def test_white_straight_promotions_round_trip(self):
        board = chess.Board("7k/4P3/7K/8/8/8/8/8 w - - 0 1")
        for uci in ["e7e8q", "e7e8r", "e7e8b", "e7e8n"]:
            with self.subTest(uci=uci):
                self.assert_round_trip(uci, board)

    def test_white_capture_promotions_round_trip(self):
        board = chess.Board("7k/3P4/7K/8/8/8/8/8 w - - 0 1")
        board.set_piece_at(chess.parse_square("c8"), chess.Piece(chess.PAWN, chess.BLACK))
        for uci in ["d7c8q", "d7c8r", "d7c8b", "d7c8n"]:
            with self.subTest(uci=uci):
                self.assert_round_trip(uci, board)

    def test_black_straight_promotions_round_trip(self):
        board = chess.Board("7k/8/8/8/8/8/4p3/7K b - - 0 1")
        for uci in ["e2e1q", "e2e1r", "e2e1b", "e2e1n"]:
            with self.subTest(uci=uci):
                self.assert_round_trip(uci, board)

    def test_black_capture_promotions_round_trip(self):
        board = chess.Board("7k/8/8/8/8/8/4p3/7K b - - 0 1")
        board.set_piece_at(chess.parse_square("d1"), chess.Piece(chess.PAWN, chess.WHITE))
        for uci in ["e2d1q", "e2d1r", "e2d1b", "e2d1n"]:
            with self.subTest(uci=uci):
                self.assert_round_trip(uci, board)

    def test_promotion_classes_are_unique_and_fit_the_expected_total(self):
        self.assertEqual(TOTAL_CLASSES, PROMOTION_OFFSET + PROMOTION_PAIR_COUNT * PROMOTION_PIECE_TYPES)
        self.assertEqual(TOTAL_CLASSES, 4272)

        promotion_moves = []
        for piece in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
            for from_square, to_square in [
                (chess.parse_square("e7"), chess.parse_square("e8")),
                (chess.parse_square("d7"), chess.parse_square("c8")),
                (chess.parse_square("e2"), chess.parse_square("e1")),
                (chess.parse_square("e2"), chess.parse_square("d1")),
            ]:
                promotion_moves.append(chess.Move(from_square, to_square, promotion=piece))

        encoded_classes = {encode_move(move) for move in promotion_moves}
        self.assertEqual(len(encoded_classes), len(promotion_moves))
        self.assertTrue(all(PROMOTION_OFFSET <= value < TOTAL_CLASSES for value in encoded_classes))


if __name__ == "__main__":
    unittest.main()
