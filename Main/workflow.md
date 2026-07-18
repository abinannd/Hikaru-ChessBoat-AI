# Phase 4 – Inference & Gameplay Workflow

## Status
NEXT PHASE

DO NOT start implementing everything at once.

This phase must be completed incrementally. Each step must be verified before moving to the next.

Maintain the existing project structure.
Do not modify or retrain the neural network.
Use the existing trained checkpoint (best_model.pth) unless explicitly instructed otherwise.

---

# Phase 4 Objectives

The goal of this phase is to transform the trained CNN into a playable chess AI capable of predicting legal chess moves for any valid board position.

The implementation must progress in the following order.

---

## Step 1 – Model Loading

Objective:
Create a reusable inference module.

Tasks:

- Load models/best_model.pth
- Reconstruct the existing CNN architecture
- Load weights correctly
- Switch model to evaluation mode
- Disable gradients using torch.no_grad()
- Verify successful loading

Verification:

✓ Checkpoint loads successfully

✓ Architecture matches training model

✓ Model enters evaluation mode

Output:

"Model successfully loaded."

---

## Step 2 – Board Input

Objective:

Accept any legal chess position.

Tasks:

- Accept FEN string input
- Validate using python-chess
- Reject invalid FENs
- Create chess.Board object
- Display board information

Verification:

Test multiple positions:

- Initial position
- Midgame
- Endgame
- Checkmate position
- Promotion position

Output:

Board parsed successfully.

---

## Step 3 – Board Encoding

Objective:

Reuse existing board_encoder.py

Tasks:

- Encode FEN
- Convert to tensor
- Shape must remain

(18,8,8)

Move tensor to GPU if CUDA available.

Verification:

Print

Input Shape

Expected Shape

Tensor Type

Device

No modifications to encoder allowed.

---

## Step 4 – Neural Network Inference

Objective:

Generate move probabilities.

Tasks:

- Forward pass
- Obtain output logits
- Confirm output size

4272

Verification:

Print:

Output shape

Highest confidence score

Top-10 predicted class indices

No move decoding yet.

---

## Step 5 – Move Decoder

Objective:

Convert predicted class IDs back into chess moves.

Reuse existing move_encoder.py

Tasks:

Decode

Class ID

↓

UCI move

Verification:

Decode several predictions.

Ensure decoded format is valid UCI.

Examples:

e2e4

g1f3

a7a8q

---

## Step 6 – Legal Move Filtering

Objective:

Never allow illegal moves.

Tasks:

Generate

board.legal_moves

For every legal move:

Encode

↓

Class ID

↓

Read corresponding network score

Select highest-scoring legal move.

Never execute illegal predictions.

Verification:

Print

Number of legal moves

Best legal move

Network score

Rejected illegal predictions

---

## Step 7 – AI Move Generator

Objective:

Create one reusable function.

Input:

Board

Output:

Best legal move

Example:

move = ai.get_best_move(board)

Verification:

Run against:

Opening

Middle game

Endgame

Check

Promotion

Castling

En-passant

---

## Step 8 – Command-Line Gameplay

Objective:

Human vs AI

Features:

Display board

Accept UCI input

Validate human move

AI responds

Print moves

Detect:

Check

Checkmate

Stalemate

Draw

Resignation (optional)

Game Over

Verification:

Complete at least one full game.

---

## Step 9 – Evaluation

Objective:

Evaluate model quality.

Tests:

Play against

Random Move Player

Simple heuristic engine

Measure:

Legal move rate

Average confidence

Game length

Wins

Losses

Draws

Save results.

---

## Step 10 – Stockfish Evaluation (Optional)

Only after Steps 1–9 are complete.

Tasks:

Play multiple games against Stockfish at low depth.

Record:

Win rate

Average centipawn loss

Move agreement

Opening performance

Endgame performance

Do NOT modify the model during evaluation.

---

## Phase 4 Deliverables

At completion, the repository should contain:

src/inference.py

src/play_cli.py

evaluation_results.txt

phase-4.md

Updated README

No retraining code.

No architecture modifications.

No dataset modifications.

---

## Future Improvements (After Phase 4)

These are NOT part of Phase 4 implementation.

Future work includes:

- Train for additional epochs
- Increase training dataset size
- Experiment with deeper CNN architectures
- Explore transformer-based chess models
- Learning rate scheduling
- Early stopping
- Model quantization
- GUI implementation (Pygame or web interface)
- Self-play reinforcement learning

---

## Important Instructions

- Work on ONLY ONE STEP at a time.
- Do NOT implement future steps before the current step is verified.
- Preserve the existing project structure.
- Reuse existing modules wherever possible.
- Do not retrain the network.
- Do not modify the CNN architecture.
- After completing each step, provide a verification report before proceeding to the next step.
