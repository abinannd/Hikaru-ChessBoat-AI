from pathlib import Path
import sys

import chess
import chess.pgn as pgn

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.board_encoder import encode_board
from src.move_encoder import TOTAL_CLASSES, decode_move, encode_move


def validate_split(path):
    with path.open("r", encoding="utf-8") as handle:
        game = pgn.read_game(handle)

        if game is None:
            raise ValueError(f"No game found in {path}")

        total_samples = 0
        board_shape_failures = 0
        move_class_failures = 0
        round_trip_failures = 0

        while game is not None:
            board = game.board()

            for move in game.mainline_moves():
                encoded_board = encode_board(board)
                board_shape_ok = encoded_board.shape == (18, 8, 8)
                if not board_shape_ok:
                    board_shape_failures += 1

                encoded_move = encode_move(move)
                move_class_ok = 0 <= encoded_move < TOTAL_CLASSES
                if not move_class_ok:
                    move_class_failures += 1

                round_trip_ok = False
                if move_class_ok:
                    try:
                        decoded_move = decode_move(encoded_move, board)
                        round_trip_ok = decoded_move is not None and decoded_move.uci() == move.uci()
                    except Exception:
                        round_trip_ok = False

                if not round_trip_ok:
                    round_trip_failures += 1

                board.push(move)
                total_samples += 1

            game = pgn.read_game(handle)

    return {
        "path": path.name,
        "total_samples": total_samples,
        "board_shape_failures": board_shape_failures,
        "move_class_failures": move_class_failures,
        "round_trip_failures": round_trip_failures,
    }


def main():
    script_dir = Path(__file__).resolve().parent.parent
    split_paths = [
        script_dir / "data" / "splits" / "train.pgn",
        script_dir / "data" / "splits" / "validation.pgn",
        script_dir / "data" / "splits" / "test.pgn",
    ]

    results = []
    combined = {
        "total_samples": 0,
        "board_shape_failures": 0,
        "move_class_failures": 0,
        "round_trip_failures": 0,
    }

    for path in split_paths:
        result = validate_split(path)
        results.append(result)
        combined["total_samples"] += result["total_samples"]
        combined["board_shape_failures"] += result["board_shape_failures"]
        combined["move_class_failures"] += result["move_class_failures"]
        combined["round_trip_failures"] += result["round_trip_failures"]

    for result in results:
        print(f"[{result['path']}] samples={result['total_samples']} board_shape_failures={result['board_shape_failures']} move_class_failures={result['move_class_failures']} round_trip_failures={result['round_trip_failures']}")

    print(
        f"[combined] samples={combined['total_samples']} board_shape_failures={combined['board_shape_failures']} "
        f"move_class_failures={combined['move_class_failures']} round_trip_failures={combined['round_trip_failures']}"
    )


if __name__ == "__main__":
    main()
