import argparse
from pathlib import Path
import sys
import time

import torch
import torch.nn as nn

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Main.chess_dataset import create_dataloaders
from Main.chess_model import ChessMoveCNN


def run_single_epoch(model, loader, criterion, optimizer, device, training: bool, limit_batches: int | None = None):
    if training:
        model.train()
    else:
        model.eval()

    total_loss = 0.0
    total_correct = 0
    total_samples = 0

    with torch.enable_grad() if training else torch.no_grad():
        for batch_idx, (inputs, targets) in enumerate(loader):
            if limit_batches is not None and batch_idx >= limit_batches:
                break
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
    parser = argparse.ArgumentParser(description="Train ChessMoveCNN on chess dataset.")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs.")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size.")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate.")
    parser.add_argument("--dry-run", action="store_true", help="Run a quick 2-epoch dry run with 2 batches per epoch to verify pipeline.")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    num_epochs = args.epochs
    batch_size = args.batch_size
    limit_batches = None

    if args.dry_run:
        print("Running in DRY-RUN mode (2 epochs, 2 batches per epoch) for pipeline verification.")
        num_epochs = 2
        limit_batches = 2

    # Load dataloaders
    train_loader = create_dataloaders(batch_size=batch_size)["train"]
    validation_loader = create_dataloaders(batch_size=batch_size)["validation"]

    model = ChessMoveCNN().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    models_dir = REPO_ROOT / "Main" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    best_val_loss = float("inf")
    best_epoch = -1
    history = []

    for epoch in range(1, num_epochs + 1):
        start_time = time.time()

        train_loss, train_acc = run_single_epoch(
            model=model,
            loader=train_loader,
            criterion=criterion,
            optimizer=optimizer,
            device=device,
            training=True,
            limit_batches=limit_batches,
        )

        val_loss, val_acc = run_single_epoch(
            model=model,
            loader=validation_loader,
            criterion=criterion,
            optimizer=None,
            device=device,
            training=False,
            limit_batches=limit_batches,
        )

        duration = time.time() - start_time

        epoch_metrics = {
            "epoch": epoch,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "train_acc": train_acc,
            "val_acc": val_acc,
            "duration": duration,
        }
        history.append(epoch_metrics)

        print(f"\nEpoch {epoch}/{num_epochs}:")
        print(f"  Training Loss: {train_loss:.4f} | Training Top-1 Acc: {train_acc * 100:.2f}%")
        print(f"  Validation Loss: {val_loss:.4f} | Validation Top-1 Acc: {val_acc * 100:.2f}%")
        print(f"  Epoch Duration: {duration:.2f}s")

        # Save checkpoint helper function
        def save_checkpoint(filepath):
            checkpoint = {
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "epoch": epoch,
                "train_loss": train_loss,
                "val_loss": val_loss,
                "train_acc": train_acc,
                "val_acc": val_acc,
            }
            torch.save(checkpoint, filepath)

        # Check if validation loss improved
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch = epoch
            best_path = models_dir / "best_model.pth"
            save_checkpoint(best_path)
            print(f"  --> Saved new best model to {best_path}")

    # Save last model checkpoint
    last_path = models_dir / "last_model.pth"
    save_checkpoint(last_path)
    print(f"  --> Saved last model to {last_path}")

    print("\n" + "="*40)
    print("TRAINING STATUS SUMMARY:")
    print(f"Best Epoch: {best_epoch}")
    print(f"Best Validation Loss: {best_val_loss:.4f}")
    print("="*40)
    
    # Final epoch metrics
    final_metrics = history[-1]
    print("Final Epoch Metrics:")
    print(f"  Epoch: {final_metrics['epoch']}")
    print(f"  Training Loss: {final_metrics['train_loss']:.4f}")
    print(f"  Validation Loss: {final_metrics['val_loss']:.4f}")
    print(f"  Training Top-1 Acc: {final_metrics['train_acc'] * 100:.2f}%")
    print(f"  Validation Top-1 Acc: {final_metrics['val_acc'] * 100:.2f}%")
    print("="*40)


if __name__ == "__main__":
    main()
