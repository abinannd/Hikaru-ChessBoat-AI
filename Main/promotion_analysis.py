from pathlib import Path

import chess.pgn


def count_promotions_in_pgn(pgn_path):
    """Count promotions in a PGN file, including promotion piece breakdown."""
    pgn_file = Path(pgn_path)
    if not pgn_file.exists():
        raise FileNotFoundError(f"PGN file not found: {pgn_file}")

    counts = {"total": 0, "q": 0, "r": 0, "b": 0, "n": 0}

    with pgn_file.open("r", encoding="utf-8") as handle:
        while True:
            game = chess.pgn.read_game(handle)
            if game is None:
                break

            for move in game.mainline_moves():
                if move.promotion is not None:
                    counts["total"] += 1
                    promo = move.promotion
                    if promo == chess.QUEEN:
                        counts["q"] += 1
                    elif promo == chess.ROOK:
                        counts["r"] += 1
                    elif promo == chess.BISHOP:
                        counts["b"] += 1
                    elif promo == chess.KNIGHT:
                        counts["n"] += 1

    return counts


def analyze_promotions(split_dir=None):
    """Analyze promotions across train, validation, and test split files."""
    if split_dir is None:
        split_dir = Path(__file__).resolve().parent / "data" / "splits"

    split_names = ["train", "validation", "test"]
    results = {}
    for name in split_names:
        results[name] = count_promotions_in_pgn(split_dir / f"{name}.pgn")

    combined = {key: 0 for key in ["total", "q", "r", "b", "n"]}
    for split_result in results.values():
        for key in combined:
            combined[key] += split_result[key]
    results["combined"] = combined
    return results


if __name__ == "__main__":
    results = analyze_promotions()
    for name in ("train", "validation", "test", "combined"):
        counts = results[name]
        print(f"{name.capitalize()} total promotions: {counts['total']}")
        print(f"{name.capitalize()} promotions to queen: {counts['q']}")
        print(f"{name.capitalize()} promotions to rook: {counts['r']}")
        print(f"{name.capitalize()} promotions to bishop: {counts['b']}")
        print(f"{name.capitalize()} promotions to knight: {counts['n']}")
        print()
