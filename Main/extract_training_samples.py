from pathlib import Path

import chess
import chess.pgn


def extract_samples_from_first_game(pgn_path=None):
    """Print board-to-move pairs from the first game in a PGN file."""
    if pgn_path is None:
        pgn_path = Path(__file__).resolve().parent / "data" / "splits" / "train.pgn"

    pgn_file = Path(pgn_path)
    if not pgn_file.exists():
        raise FileNotFoundError(f"PGN file not found: {pgn_file}")

    with pgn_file.open("r", encoding="utf-8") as handle:
        game = chess.pgn.read_game(handle)

    if game is None:
        raise ValueError("No game found in PGN file")

    board = game.board()
    for move_number, move in enumerate(game.mainline_moves(), start=1):
        print(f"Sample {move_number}:")
        print(f"FEN: {board.fen()}")
        print(f"UCI: {move.uci()}")
        board.push(move)
        print()


if __name__ == "__main__":
    extract_samples_from_first_game()
