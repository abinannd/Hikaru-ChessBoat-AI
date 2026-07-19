import argparse
import hashlib
import os
from pathlib import Path
import sys
import time

import torch
import torch.nn as nn

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.chess_dataset import create_dataloaders
from src.chess_model import ChessMoveCNN

def get_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def run_single_epoch(model, loader, criterion, optimizer, device, training: bool, limit_batches: int | None = None, scaler=None):
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
                if scaler is not None:
                    # Enable AMP mixed precision
                    with torch.amp.autocast(device_type=device.type):
                        logits = model(inputs)
                        loss = criterion(logits, targets)
                    scaler.scale(loss).backward()
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    logits = model(inputs)
                    loss = criterion(logits, targets)
                    loss.backward()
                    optimizer.step()
            else:
                if scaler is not None:
                    with torch.amp.autocast(device_type=device.type):
                        logits = model(inputs)
                        loss = criterion(logits, targets)
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
    print("Loading dataloaders...")
    loaders = create_dataloaders(batch_size=batch_size)
    train_loader = loaders["train"]
    validation_loader = loaders["validation"]

    train_size = len(train_loader.dataset)
    val_size = len(validation_loader.dataset)

    model = ChessMoveCNN().to(device)
    params_count = sum(p.numel() for p in model.parameters())
    print(f"Model design: ChessMoveCNN with {params_count:,} parameters.")

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    
    # Initialize scaler for mixed precision (AMP) if using CUDA
    scaler = torch.amp.GradScaler("cuda") if device.type == "cuda" else None
    if scaler is not None:
        print("AMP Mixed Precision enabled.")

    # Learning rate scheduler
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=1)
    print("ReduceLROnPlateau scheduler active (patience=1, factor=0.5).")

    # Early stopping config
    early_stopping_patience = 3
    epochs_no_improve = 0

    models_dir = REPO_ROOT / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    best_val_loss = float("inf")
    best_epoch = -1
    best_train_loss = 0.0
    best_train_acc = 0.0
    best_val_acc = 0.0
    
    history = []
    total_training_start = time.time()

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
            scaler=scaler,
        )

        val_loss, val_acc = run_single_epoch(
            model=model,
            loader=validation_loader,
            criterion=criterion,
            optimizer=None,
            device=device,
            training=False,
            limit_batches=limit_batches,
            scaler=scaler,
        )

        duration = time.time() - start_time
        current_lr = optimizer.param_groups[0]["lr"]

        epoch_metrics = {
            "epoch": epoch,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "train_acc": train_acc,
            "val_acc": val_acc,
            "duration": duration,
            "lr": current_lr
        }
        history.append(epoch_metrics)

        print(f"\nEpoch {epoch}/{num_epochs}:")
        print(f"  Training Loss: {train_loss:.4f} | Training Top-1 Acc: {train_acc * 100:.2f}%")
        print(f"  Validation Loss: {val_loss:.4f} | Validation Top-1 Acc: {val_acc * 100:.2f}%")
        print(f"  Learning Rate: {current_lr:.6f} | Epoch Duration: {duration:.2f}s")

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
            best_train_loss = train_loss
            best_train_acc = train_acc
            best_val_acc = val_acc
            
            best_path = models_dir / "best_model.pth"
            save_checkpoint(best_path)
            print(f"  --> Saved new best model to {best_path}")
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            print(f"  --> No validation loss improvement for {epochs_no_improve} epoch(s)")

        # Step LR Scheduler
        scheduler.step(val_loss)

        # Early stopping check
        if epochs_no_improve >= early_stopping_patience and not args.dry_run:
            print(f"\nEarly stopping triggered! No improvement for {early_stopping_patience} consecutive epochs.")
            break

    total_training_time = time.time() - total_training_start

    # Save last model checkpoint
    last_path = models_dir / "last_model.pth"
    save_checkpoint(last_path)
    print(f"  --> Saved last model to {last_path}")

    # Generate metadata files if not a dry-run
    if not args.dry_run:
        # Get hash and size details
        best_hash = get_sha256(best_path)
        best_size = os.path.getsize(best_path)
        last_hash = get_sha256(last_path)
        last_size = os.path.getsize(last_path)

        # 1. Write checkpoint_info.txt
        checkpoint_info_path = models_dir / "checkpoint_info.txt"
        with checkpoint_info_path.open("w", encoding="utf-8") as f:
            f.write(f"=== Information stored in best_model.pth ===\n")
            f.write(f"SHA256 Hash: {best_hash}\n")
            f.write(f"File Size: {best_size:,} bytes\n")
            f.write(f"Stored Epoch: {best_epoch}\n")
            f.write(f"Stored Training Loss: {best_train_loss}\n")
            f.write(f"Stored Validation Loss: {best_val_loss}\n")
            f.write(f"Stored Training Accuracy: {best_train_acc * 100:.2f}%\n")
            f.write(f"Stored Validation Accuracy: {best_val_acc * 100:.2f}%\n")
            f.write(f"Creation Time: {time.ctime(os.path.getctime(best_path))}\n")
            f.write(f"Modification Time: {time.ctime(os.path.getmtime(best_path))}\n\n")
            
            f.write(f"=== Information stored in last_model.pth ===\n")
            f.write(f"SHA256 Hash: {last_hash}\n")
            f.write(f"File Size: {last_size:,} bytes\n")
            f.write(f"Stored Epoch: {history[-1]['epoch']}\n")
            f.write(f"Stored Training Loss: {history[-1]['train_loss']}\n")
            f.write(f"Stored Validation Loss: {history[-1]['val_loss']}\n")
            f.write(f"Stored Training Accuracy: {history[-1]['train_acc'] * 100:.2f}%\n")
            f.write(f"Stored Validation Accuracy: {history[-1]['val_acc'] * 100:.2f}%\n")
            f.write(f"Creation Time: {time.ctime(os.path.getctime(last_path))}\n")
            f.write(f"Modification Time: {time.ctime(os.path.getmtime(last_path))}\n")
        print(f"Created metadata: {checkpoint_info_path}")

        # 2. Write training_summary.txt
        training_summary_path = models_dir / "training_summary.txt"
        total_time_hours = total_training_time / 3600
        total_time_mins = (total_training_time % 3600) / 60
        total_time_secs = total_training_time % 60
        
        with training_summary_path.open("w", encoding="utf-8") as f:
            f.write(f"Project name: Hikaru Chess AI\n")
            f.write(f"Training date: {time.strftime('%Y-%m-%d')}\n")
            f.write(f"Total epochs: {history[-1]['epoch']}\n")
            f.write(f"Total training time: {total_training_time:.2f} seconds ({int(total_time_hours)} hours, {int(total_time_mins)} minutes, {total_time_secs:.2f} seconds)\n")
            f.write(f"Best epoch: {best_epoch}\n")
            f.write(f"Best validation loss: {best_val_loss:.6f}\n")
            f.write(f"Best validation accuracy: {best_val_acc:.6f} (Epoch {best_epoch} had {best_val_acc*100:.2f}% accuracy)\n")
            f.write(f"Final epoch metrics:\n")
            f.write(f"  Epoch: {history[-1]['epoch']}\n")
            f.write(f"  Training Loss: {history[-1]['train_loss']:.6f}\n")
            f.write(f"  Validation Loss: {history[-1]['val_loss']:.6f}\n")
            f.write(f"  Training Top-1 Accuracy: {history[-1]['train_acc']*100:.2f}%\n")
            f.write(f"  Validation Top-1 Accuracy: {history[-1]['val_acc']*100:.2f}%\n")
            f.write(f"  Duration: {history[-1]['duration']:.2f} seconds\n")
            f.write(f"CNN parameter count: {params_count:,} parameters\n")
            f.write(f"Dataset sizes:\n")
            f.write(f"  Training dataset: {train_size:,} samples\n")
            f.write(f"  Validation dataset: {val_size:,} samples\n")
            f.write(f"Batch size: {batch_size}\n")
            f.write(f"Optimizer: Adam (initial learning rate = {args.lr})\n")
            f.write(f"Loss function: CrossEntropyLoss\n")
            f.write(f"GPU used: {torch.cuda.get_device_name(0) if device.type == 'cuda' else 'CPU'}\n")
            f.write(f"PyTorch version: {torch.__version__}\n")
        print(f"Created metadata: {training_summary_path}")

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
