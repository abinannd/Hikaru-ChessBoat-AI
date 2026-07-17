from pathlib import Path
import sys

import torch
import torch.nn as nn

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Main.chess_dataset import create_dataloaders
from Main.chess_model import ChessMoveCNN


def run_single_epoch(model, loader, criterion, optimizer, device, training: bool):
    if training:
        model.train()
    else:
        model.eval()

    total_loss = 0.0
    total_correct = 0
    total_samples = 0

    with torch.enable_grad() if training else torch.no_grad():
        for inputs, targets in loader:
            inputs = inputs.to(device, non_blocking=True)
            targets = targets.to(device, non_blocking=True)

            if training:
                optimizer.zero_grad(set_to_none=True)
                logits = model(inputs)
                loss = criterion(logits, targets)
                loss.backward()
                optimizer.step()
            else:
                logits = model(inputs)
                loss = criterion(logits, targets)

            batch_size = targets.size(0)
            total_samples += batch_size
            total_loss += loss.item() * batch_size

            predictions = logits.argmax(dim=1)
            total_correct += (predictions == targets).sum().item()

    avg_loss = total_loss / max(total_samples, 1)
    accuracy = total_correct / max(total_samples, 1)
    return avg_loss, accuracy


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    train_loader = create_dataloaders(batch_size=32)["train"]
    validation_loader = create_dataloaders(batch_size=32)["validation"]

    model = ChessMoveCNN().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    train_loss, train_acc = run_single_epoch(
        model=model,
        loader=train_loader,
        criterion=criterion,
        optimizer=optimizer,
        device=device,
        training=True,
    )

    val_loss, val_acc = run_single_epoch(
        model=model,
        loader=validation_loader,
        criterion=criterion,
        optimizer=None,
        device=device,
        training=False,
    )

    print(f"Average training loss: {train_loss:.4f}")
    print(f"Average validation loss: {val_loss:.4f}")
    print(f"Training top-1 accuracy: {train_acc * 100:.2f}%")
    print(f"Validation top-1 accuracy: {val_acc * 100:.2f}%")


if __name__ == "__main__":
    main()
