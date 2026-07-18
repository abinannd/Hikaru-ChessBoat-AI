import random
from pathlib import Path

import chess.pgn


def write_split_files(output_dir, train_games, val_games, test_games):
    """Write train/validation/test games to separate PGN files in the given directory."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = {}
    for name, games in (("train", train_games), ("validation", val_games), ("test", test_games)):
        file_path = output_dir / f"{name}.pgn"
        with file_path.open("w", encoding="utf-8") as handle:
            for game in games:
                export_game = game
                if hasattr(game, "headers"):
                    export_game = game
                handle.write(str(export_game))
                if not str(export_game).endswith("\n"):
                    handle.write("\n")
        paths[name] = file_path

    return paths


def verify_saved_split_files(split_dir, expected_sizes=None):
    """Read back the saved split PGN files with python-chess and verify game counts."""
    split_dir = Path(split_dir)
    if expected_sizes is None:
        expected_sizes = {"train": 2988, "validation": 374, "test": 374}

    results = {}
    for name in ("train", "validation", "test"):
        file_path = split_dir / f"{name}.pgn"
        if not file_path.exists():
            raise FileNotFoundError(f"Split file not found: {file_path}")

        with file_path.open("r", encoding="utf-8") as handle:
            parsed_count = 0
            while True:
                try:
                    game = chess.pgn.read_game(handle)
                except Exception:
                    break

                if game is None:
                    break

                parsed_count += 1

        matches_expected = parsed_count == expected_sizes[name]
        results[name] = {
            "file": file_path,
            "count": parsed_count,
            "expected": expected_sizes[name],
            "matches_expected": matches_expected,
        }

    return results


def count_games_by_ply_threshold(pgn_path=None):
    """Stream games from a PGN file and count accepted/rejected games based on a 20+ ply threshold."""
    accepted_games, rejected = collect_accepted_games(pgn_path)
    return len(accepted_games), rejected


def collect_accepted_games(pgn_path=None):
    """Collect only the accepted games with 20 or more plies."""
    if pgn_path is None:
        pgn_path = Path(__file__).with_name("game-3K.pgn")

    pgn_file = Path(pgn_path)
    if not pgn_file.exists():
        raise FileNotFoundError(f"PGN file not found: {pgn_file}")

    accepted_games = []
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
                accepted_games.append(game)
            else:
                rejected += 1

    return accepted_games, rejected


def create_split_sets(accepted_games, train_size=2988, val_size=374, test_size=374):
    """Shuffle accepted games with a fixed seed and split them into train/validation/test sets."""
    shuffled_games = accepted_games[:]
    random.Random(42).shuffle(shuffled_games)

    train_games = shuffled_games[:train_size]
    val_games = shuffled_games[train_size : train_size + val_size]
    test_games = shuffled_games[train_size + val_size : train_size + val_size + test_size]

    return train_games, val_games, test_games


def main():
    try:
        accepted_games, rejected = collect_accepted_games()
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        return 1

    accepted_count = len(accepted_games)
    print(f"Accepted games (20+ plies): {accepted_count}")
    print(f"Rejected games (<20 plies): {rejected}")

    train_games, val_games, test_games = create_split_sets(accepted_games)
    print(f"Training set: {len(train_games)}")
    print(f"Validation set: {len(val_games)}")
    print(f"Test set: {len(test_games)}")
    print(f"Total assigned: {len(train_games) + len(val_games) + len(test_games)}")

    split_dir = Path(__file__).resolve().parent / "splits"
    paths = write_split_files(split_dir, train_games, val_games, test_games)
    print(f"Wrote training games to: {paths['train']}")
    print(f"Wrote validation games to: {paths['validation']}")
    print(f"Wrote test games to: {paths['test']}")
    print(f"Training file games: {len(train_games)}")
    print(f"Validation file games: {len(val_games)}")
    print(f"Test file games: {len(test_games)}")

    verification_results = verify_saved_split_files(split_dir)
    for name in ("train", "validation", "test"):
        result = verification_results[name]
        print(f"Verified {name} file games: {result['count']}")
        print(f"{name.capitalize()} count matches expected: {result['matches_expected']}")

    train_ids = {id(game) for game in train_games}
    val_ids = {id(game) for game in val_games}
    test_ids = {id(game) for game in test_games}
    no_overlap = train_ids.isdisjoint(val_ids) and train_ids.isdisjoint(test_ids) and val_ids.isdisjoint(test_ids)
    print(f"No overlap between sets: {no_overlap}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
