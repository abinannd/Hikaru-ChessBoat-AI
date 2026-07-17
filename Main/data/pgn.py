from pathlib import Path
import chess.pgn


def count_games_by_ply_threshold(pgn_path=None):
    """Stream games from a PGN file and count accepted/rejected games based on a 20+ ply threshold."""
    if pgn_path is None:
        pgn_path = Path(__file__).with_name("game-3K.pgn")

    pgn_file = Path(pgn_path)
    if not pgn_file.exists():
        raise FileNotFoundError(f"PGN file not found: {pgn_file}")

    accepted = 0
    rejected = 0

    with pgn_file.open("r", encoding="utf-8") as handle:
        while True:
            try:
                game = chess.pgn.read_game(handle)
            except Exception:
                # Skip malformed game data without crashing the whole program.
                break

            if game is None:
                break

            plies = len(list(game.mainline_moves()))
            if plies >= 20:
                accepted += 1
            else:
                rejected += 1

    return accepted, rejected


def main():
    try:
        accepted, rejected = count_games_by_ply_threshold()
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        return 1

    print(f"Accepted games (20+ plies): {accepted}")
    print(f"Rejected games (<20 plies): {rejected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
