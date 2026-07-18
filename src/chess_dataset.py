from pathlib import Path
from typing import List, Tuple

import chess.pgn
import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset

try:
    from .board_encoder import encode_board
    from .move_encoder import TOTAL_CLASSES, encode_move
except ImportError:  # pragma: no cover - allows running the file directly
    from src.board_encoder import encode_board
    from src.move_encoder import TOTAL_CLASSES, encode_move


class ChessPGNDataset(Dataset):
    """Lazy-loading chess dataset that encodes board states and target moves on demand."""

    def __init__(self, split_name: str, data_dir: str | Path | None = None):
        if split_name not in {"train", "validation", "test"}:
            raise ValueError("split_name must be one of: train, validation, test")

        if data_dir is None:
            data_dir = Path(__file__).resolve().parent.parent / "data" / "splits"
        self.data_dir = Path(data_dir)
        self.split_name = split_name
        self.pgn_path = self.data_dir / f"{split_name}.pgn"

        if not self.pgn_path.exists():
            raise FileNotFoundError(f"PGN file not found: {self.pgn_path}")

        self.samples: List[Tuple[int, int]] = self._build_sample_index()

    def _build_sample_index(self) -> List[Tuple[int, int]]:
        """Create lightweight metadata for each sample as (game_offset, plies_before_move)."""
        sample_index: List[Tuple[int, int]] = []
        with self.pgn_path.open("r", encoding="utf-8") as handle:
            while True:
                game_offset = handle.tell()
                game = chess.pgn.read_game(handle)
                if game is None:
                    break

                move_list = list(game.mainline_moves())
                for ply_index in range(len(move_list)):
                    sample_index.append((game_offset, ply_index))

        return sample_index

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> Tuple[torch.Tensor, torch.Tensor]:
        if index < 0 or index >= len(self.samples):
            raise IndexError(f"Dataset index {index} is out of range for split {self.split_name}")

        game_offset, plies_before_move = self.samples[index]
        with self.pgn_path.open("r", encoding="utf-8") as handle:
            handle.seek(game_offset)
            game = chess.pgn.read_game(handle)
            if game is None:
                raise ValueError(f"Unable to read game at offset {game_offset} in {self.pgn_path}")

            board = game.board()
            move_list = list(game.mainline_moves())
            for move_index in range(plies_before_move):
                board.push(move_list[move_index])

            target_move = move_list[plies_before_move]
            board_state = encode_board(board)
            move_class = encode_move(target_move)

        if not 0 <= move_class <= TOTAL_CLASSES - 1:
            raise ValueError(f"Encoded move class {move_class} is out of range for split {self.split_name}")

        board_tensor = torch.from_numpy(board_state.astype(np.float32, copy=False))
        target_tensor = torch.tensor(move_class, dtype=torch.long)
        return board_tensor, target_tensor


def create_dataloaders(
    batch_size: int = 32,
    data_dir: str | Path | None = None,
    num_workers: int = 0,
) -> dict[str, DataLoader]:
    """Create train/validation/test DataLoaders for the split PGN files."""
    if data_dir is None:
        data_dir = Path(__file__).resolve().parent.parent / "data" / "splits"

    datasets = {
        "train": ChessPGNDataset("train", data_dir=data_dir),
        "validation": ChessPGNDataset("validation", data_dir=data_dir),
        "test": ChessPGNDataset("test", data_dir=data_dir),
    }

    pin_memory = torch.cuda.is_available()
    dataloaders = {
        "train": DataLoader(
            datasets["train"],
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
            pin_memory=pin_memory,
        ),
        "validation": DataLoader(
            datasets["validation"],
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=pin_memory,
        ),
        "test": DataLoader(
            datasets["test"],
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=pin_memory,
        ),
    }
    return dataloaders


def verify_dataloaders(batch_size: int = 32, data_dir: str | Path | None = None) -> None:
    """Load one batch from each split and print dataset and batch metadata."""
    dataloaders = create_dataloaders(batch_size=batch_size, data_dir=data_dir)

    for split_name, loader in dataloaders.items():
        dataset = loader.dataset
        board_batch, target_batch = next(iter(loader))

        if board_batch.ndim != 4:
            raise ValueError(f"Unexpected board batch shape {tuple(board_batch.shape)}")
        if target_batch.ndim != 1:
            raise ValueError(f"Unexpected target batch shape {tuple(target_batch.shape)}")

        target_values = target_batch.cpu().numpy()
        print(f"{split_name.upper()} dataset size: {len(dataset)}")
        print(f"  board batch shape: {tuple(board_batch.shape)}")
        print(f"  board dtype: {board_batch.dtype}")
        print(f"  target batch shape: {tuple(target_batch.shape)}")
        print(f"  target dtype: {target_batch.dtype}")
        print(f"  target min/max: {int(target_values.min())}/{int(target_values.max())}")
        if not np.all((target_values >= 0) & (target_values <= TOTAL_CLASSES - 1)):
            raise ValueError(f"Target classes outside 0..{TOTAL_CLASSES - 1} for {split_name}")
        print(f"  target range valid: True")


if __name__ == "__main__":
    verify_dataloaders(batch_size=32)
