# Phase 10 – Step 2 Verification Report

This report documents the design, implementation, and verification details of the captured pieces panels and material balance indicator.

---

## ♟️ Capture Calculation

- **No Manual Lists**: The list of captured pieces is never tracked manually. This prevents out-of-sync states upon undos, redos, or resets.
- **Starting counts comparison**: Derived directly from the active board state by scanning the board squares, counting the remaining pieces of each type/color, and subtracting this from standard starting piece counts:
  - White piece captured count = $Starting[White][PieceType] - Remaining[White][PieceType]$ (displays in Black's captures).
  - Black piece captured count = $Starting[Black][PieceType] - Remaining[Black][PieceType]$ (displays in White's captures).

---

## 📐 Material Balance

- **Formula**: Net material score calculated from White's perspective using standard piece weights:
  - Pawn: 1, Knight: 3, Bishop: 3, Rook: 5, Queen: 9.
  - $MaterialBalance = \sum(WhitePieces) - \sum(BlackPieces)$.
- ** Advantage Display**: 
  - If balance is positive ($>0$), White has a material advantage: display `+balance` in White's label.
  - If balance is negative ($<0$), Black has a material advantage: display `+abs(balance)` in Black's label.
  - Display nothing if balance is 0.

---

## 🎨 GUI Layout

- **Side Panel Placement**: Placed the two horizontal panels above the Move History scroll panel.
- **Piece Widget Recycling**: Populated using small width-constrained instances of the standard `ChessPiece` widget, displaying standard unicode symbols (`♝`, `♞`, etc.) matching the active board style.
- **Ordering**: Captured pieces are grouped in order: Queen, Rook, Bishop, Knight, Pawn.

---

## 🔄 Synchronization Workflow

- **Centralized Hook**: Hooked `refresh_captured_pieces()` directly into the `update_game_status()` sequence.
- **Universal updates**: Runs automatically after human moves, AI moves, undos, redos, resets (new game), and promotion dialog selections.

---

## 📋 Verification Checklist

- [x] **Captures Displayed Correctly**: Shows Black pieces captured by White, and White pieces captured by Black.
- [x] **Stable Sorting**: Pieces remain consistently sorted: Queen $\to$ Rook $\to$ Bishop $\to$ Knight $\to$ Pawn.
- [x] **Undo Reverts Panel**: Undoing a capture removes the piece from the captured panel instantly.
- [x] **Redo Restores Panel**: Redoing a capture updates the panel.
- [x] **Promotion Correctness**: Promoting a pawn reduces the pawn count and increases the queen (or chosen piece) count in the active list correctly.
- [x] **New Game Clears Panels**: Restarts clear both box layouts.
- [x] **Material Balance Correctness**: Score indicator adds and subtracts values exactly as expected.
- [x] **Responsive Resizing**: Box layout structures flow and scale smoothly within the side panel bounds.
- [x] **No State Duplication**: Derives exclusively from python-chess board representation.
- [x] **No AI Engine Modifications**: AI weights and model parameters are kept completely isolated.
