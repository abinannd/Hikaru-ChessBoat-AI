# Phase 9 – Step 2 Verification Report

This report documents the design, implementation, and verification details of the Undo / Redo system in the GUI.

---

## ↩️ Undo Workflow

The Undo mechanism leverages the `python-chess` board stack dynamically:
- **Human vs Human Mode**: Pops exactly one move (`board.pop()`) and pushes it onto `self.redo_stack`.
- **Human vs AI Mode** (when AI engine is active): Pops exactly two moves (the AI's response move first, and then the Human's origin move) to revert the state back to the start of the human player's turn. Both popped moves are appended to `self.redo_stack` (AI move `m2` first, then Human move `m1` so that `m1` sits on top).
- **GUI Refresh**: Triggers `load_position(board)` to update the piece widgets, then updates the status bar and history logs.

---

## 🔁 Redo Workflow

The Redo mechanism reapplies moves from the local stack:
- **Redo Stack**: Maintains `self.redo_stack = []` (list of standard `chess.Move` objects).
- **Human vs Human Mode**: Pops the latest move from `self.redo_stack`, generates its SAN notation relative to the current position, and pushes it onto the board.
- **Human vs AI Mode**: Pops two moves from `self.redo_stack` (the Human move first, and then the AI response move). Each move has its SAN notation calculated dynamically in context before being pushed onto the board.
- **New Move Interlock**: Whenever a new human move is played, `self.clear_redo_stack()` is called to empty the stack and update button disabled states.

---

## 🔄 Synchronization Strategy

- **Move History Sync**:
  - `undo_move()` pops 1 (or 2) moves off `self.move_history_list` to maintain strict length parity.
  - `redo_move()` appends the newly computed SAN values back onto `self.move_history_list`.
  - Both call `refresh_history_panel()` to redraw the column text log.
- **Game Status Sync**: Re-evaluates check and turn indicators immediately after popping or pushing.
- **Button Disabled States**:
  - `Undo` button disables if `self.can_undo()` is False (move stack length $<1$ for HvH, or $<2$ for HvA).
  - `Redo` button disables if `self.can_redo()` is False (redo stack length $<1$ for HvH, or $<2$ for HvA).
  - Updated automatically on move executions, undos, redos, and new game resets.

---

## 📋 Verification Checklist

- [x] **Undo in Human vs Human**: Pops and reverts 1 move correctly.
- [x] **Undo in Human vs AI**: Pops and reverts both human move and AI response move in a single click.
- [x] **Redo Restores Moves**: Re-applies popped moves in correct chronological order.
- [x] **Move History Updates**: History panel synchronizes (removes on undo, appends on redo) with correct notation and numbering.
- [x] **Redo Stack Clears**: Making a new move after undoing successfully empties the redo stack.
- [x] **Buttons Enable/Disable**: Buttons gray out correctly when no moves are available in the respective stacks.
- [x] **No State Cloning**: Reuses only python-chess `board.pop()` and `board.push()`, ensuring no duplicated board objects.
- [x] **AI Stays Synced**: Game state checks and device settings remain unaffected.
