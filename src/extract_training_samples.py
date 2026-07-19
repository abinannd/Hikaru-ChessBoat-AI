from pathlib import Path

import chess.pgn


def count_samples_in_pgn(pgn_path):
    """Count board-to-move samples (plies) in a PGN file."""
    pgn_file = Path(pgn_path)
    if not pgn_file.exists():
        raise FileNotFoundError(f"PGN file not found: {pgn_file}")

    sample_count = 0
    with pgn_file.open("r", encoding="utf-8") as handle:
        while True:
            game = chess.pgn.read_game(handle)
            if game is None:
                break
            sample_count += len(list(game.mainline_moves()))

    return sample_count


def count_samples_in_splits(split_dir=None):
    """Count position-to-next-move samples for each split and combined total."""
    if split_dir is None:
        split_dir = Path(__file__).resolve().parent.parent / "data" / "splits"

    split_names = ["train", "validation", "test"]
    counts = {}
    for name in split_names:
        counts[name] = count_samples_in_pgn(split_dir / f"{name}.pgn")

    counts["combined"] = sum(counts.values())
    return counts


def main():
    counts = count_samples_in_splits()
    print(f"Training samples: {counts['train']}")
    print(f"Validation samples: {counts['validation']}")
    print(f"Test samples: {counts['test']}")
    print(f"Combined total: {counts['combined']}")


if __name__ == "__main__":
    main()
