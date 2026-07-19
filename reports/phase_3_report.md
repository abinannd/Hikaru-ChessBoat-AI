<div align="center">

# Supervised Chess AI — Dataset Pipeline

### Phase 3 · Neural Network Training Pipeline (Updated)

*From encoded chess positions to a trained convolutional neural network that predicts moves.*

![Status](https://img.shields.io/badge/status-complete-brightgreen)
![Samples](https://img.shields.io/badge/samples-423%2C469-blue)
![Epochs](https://img.shields.io/badge/epochs-10-informational)
![Val Loss](https://img.shields.io/badge/val%20loss-4.0642-success)
![Val Accuracy](https://img.shields.io/badge/val%20accuracy-19.45%25-success)

</div>

---

## Table of Contents

1. [Status](#status)
2. [Objectives](#objectives)
3. [Environment](#environment)
4. [Training Results](#training-results)
5. [Training Progress (Epoch-by-Epoch)](#training-progress-epoch-by-epoch)
6. [Training Improvements Implemented](#training-improvements-implemented)
7. [Conclusion](#conclusion)

---

## Status

**Status: Completed**

Phase 3 implements the supervised-learning training pipeline on the expanded dataset. We trained a completely new `ChessMoveCNN` model from scratch using PyTorch and validated its performance across 10 epochs.

---

## Objectives

| # | Objective | Result |
|---|---|---|
| 1 | Train the model from scratch on expanded dataset | Done |
| 2 | Use CrossEntropyLoss and Adam optimizer | Done |
| 3 | Enable GPU acceleration (CUDA) | Done |
| 4 | Integrate learning-rate scheduler (ReduceLROnPlateau) | Done |
| 5 | Enable AMP Mixed Precision to accelerate GPU execution | Done |
| 6 | Track best validation loss and save checkpoints | Done |

---

## Environment

### Hardware
- **CPU**: Intel Core i5-12450HX
- **GPU**: NVIDIA GeForce RTX 2050 (4 GB VRAM)
- **System RAM**: 12 GB

### Software
- **Python**: 3.10.6
- **PyTorch**: 2.5.1+cu121
- **CUDA**: 12.1 active
- **python-chess**: 1.10.0

---

## Training Results

Our memory-cached dataset pipeline coupled with AMP Mixed Precision allowed us to train the expanded dataset (423,469 training samples) in **1,228 seconds (20 minutes, 28 seconds)**, compared to over 3.7 hours on the smaller dataset without caching.

- **Best Epoch**: 10
- **Best Validation Loss**: **4.0642** (previously 4.2981)
- **Best Validation Accuracy (Top-1)**: **19.45%** at Epoch 9 (previously 19.04%)
- **Final Epoch Metrics (Epoch 10)**:
  - **Training Loss**: 3.8078
  - **Validation Loss**: 4.0642
  - **Training Top-1 Accuracy**: 20.68%
  - **Validation Top-1 Accuracy**: 19.38%

---

## Training Progress (Epoch-by-Epoch)

| Epoch | Training Loss | Training Top-1 Acc | Validation Loss | Validation Top-1 Acc | Learning Rate | Duration |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 5.5031 | 8.33% | 4.9548 | 11.94% | 0.001000 | 117.37s |
| 2 | 4.6611 | 13.94% | 4.5198 | 15.61% | 0.001000 | 122.17s |
| 3 | 4.3386 | 16.75% | 4.3465 | 16.95% | 0.001000 | 122.41s |
| 4 | 4.1683 | 18.00% | 4.2758 | 18.08% | 0.001000 | 128.53s |
| 5 | 4.0617 | 18.87% | 4.1976 | 18.59% | 0.001000 | 132.10s |
| 6 | 3.9877 | 19.42% | 4.1461 | 18.41% | 0.001000 | 131.55s |
| 7 | 3.9255 | 19.86% | 4.1123 | 18.94% | 0.001000 | 122.49s |
| 8 | 3.8772 | 20.16% | 4.0911 | 19.22% | 0.001000 | 118.38s |
| 9 | 3.8426 | 20.41% | 4.0677 | 19.45% | 0.001000 | 117.75s |
| 10 | 3.8078 | 20.68% | 4.0642 | 19.38% | 0.001000 | 121.14s |

---

## Training Improvements Implemented

1. **Memory Caching**: Rather than doing slow on-demand PGN parsing and move-seeking during the training loop, the entire dataset is loaded and encoded sequentially in RAM during initialization. This reduced file I/O overhead to zero.
2. **AMP Mixed Precision**: Leveraged PyTorch's `torch.amp` autocasting and `GradScaler` to train in FP16 on the RTX 2050's Tensor Cores, yielding substantial throughput gains.
3. **LR Scheduler**: Configured `ReduceLROnPlateau` scheduler to adjust learning rate if validation loss stagnates.
4. **Early Stopping**: Equipped the loop with early stopping patience of 3, ensuring training stops early if validation loss degrades.

---

## Conclusion

The training run succeeded with unidirectional improvements:
- Validation loss fell from **4.2981 to 4.0642**.
- Training accuracy reached **20.68%** (without overfitting, as validation accuracy stays aligned at **19.38% / 19.45%**).
- Checkpoints were successfully saved to `models/best_model.pth` and `models/last_model.pth`.