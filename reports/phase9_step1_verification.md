# Phase 9 – Step 1 Verification Report

This report documents the design, implementation, and verification details of the move history panel (SAN/PGN) in the GUI.

---

## ♟️ SAN Generation

Standard Algebraic Notation (SAN) strings are generated dynamically using `python-chess` API calls:
- **Prior Context Dependency**: The SAN notation must be resolved before executing the move on the board (e.g. check status, disambiguations). Therefore, `san_str = board.san(move)` is invoked immediately before calling `board.push(move)`.
- **Automatic formatting**: python-chess automatically resolves captures (`x`), promotions (`=Q`), castling (`O-O` / `O-O-O`), checks (`+`), and checkmate (`#`) without manual string parsing.

---

## 📐 History Architecture

The move history system follows a clean object-oriented layout inside `MainWindow`:
- **Data Store**: Maintains `self.move_history_list = []` (list of all moves in order).
- **Core Interfaces**:
  - `add_move_to_history(san_str)`: Appends the SAN string to the array and calls refresh.
  - `clear_history()`: Resets `self.move_history_list` to `[]` and refreshes.
  - `refresh_history_panel()`: Refreshes the display text structure and scrolls the panel.
- **Move Numbering**: Formats moves into standard double-column rows:
  - Format: `[move_num].  [white_move]  [black_move]` (e.g., `1.  e4        e5`).
  - Leaves the Black column empty if the match finishes after White's turn.

---

## 🔄 Synchronization Workflow

The history panel stays synchronized with all gameplay events:
- **Human Turns**: `ChessBoard.handle_square_click()` resolves the SAN, executes the move, and triggers `on_move_executed_callback(move, san_str)`. The handler calls `add_move_to_history(san_str)`.
- **AI Turns**: `MainWindow.execute_ai_move()` calculates the SAN, pushes the AI move, and calls `add_move_to_history(san_str)` directly.
- **Game Resets**: Pressing **"New Game"** triggers `clear_history()`, resetting the move list and emptying the display panel text.

---

## 🎨 GUI Layout

- **Side Panel Placement**: Replaced the static move history label placeholder with a custom scrollable panel.
- **`ScrollableLabel` Widget**: Extends Kivy's `ScrollView`. Contains a multiline `Label` whose height is bound dynamically to the text `texture_size` (`self.label.bind(texture_size=self.label.setter('size'))`), and wrapping is handled via width bindings.
- **Auto-scroll**: The scroll view automatically shifts focus to the bottom (`self.history_scroll.scroll_y = 0.0`) after additions, ensuring the newest moves are always visible while older logs can be reviewed by manual scrolling.

---

## 📋 Verification Checklist

- [x] **Human Moves Recorded**: Human pawn and knight moves populate the log correctly.
- [x] **AI Moves Recorded**: AI responses show up automatically next to human moves.
- [x] **SAN Notation Correct**: Displays standard symbols like `Nf3`, `e4`, `O-O`, etc.
- [x] **Standard Move Numbering**: Moves are paired on the same row with correct indices.
- [x] **New Game Resets Panel**: Clicking New Game clears all text in the scroll panel.
- [x] **Dynamic Scrolling**: Scrollbar appears when history height exceeds container size, auto-scrolling to the bottom.
- [x] **No Duplicate Entries**: Checked sequence; move list and display log contain no duplicate records.
- [x] **No AI Engine Modifications**: AI prediction pipelines remain unchanged.
- [x] **Read-Only**: Move history text is read-only and not editable by the user.
