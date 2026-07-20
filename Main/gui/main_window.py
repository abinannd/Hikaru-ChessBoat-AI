import sys
from pathlib import Path

# Resolve repository root to allow importing src modules
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Resolve local gui folder to allow importing relative components
GUI_ROOT = Path(__file__).resolve().parent
if str(GUI_ROOT) not in sys.path:
    sys.path.insert(0, str(GUI_ROOT))

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from chess_board import ChessBoard

# Import python-chess
import chess

class ScrollableLabel(ScrollView):
    """Scrollable panel to display move logs in standard format."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.label = Label(
            text="",
            font_size='14sp',
            size_hint_y=None,
            halign='left',
            valign='top',
            padding=(10, 10)
        )
        # Bind the label height to its text height for dynamic scrolling
        self.label.bind(texture_size=self.label.setter('size'))
        # Bind ScrollView width to label bounds for wrapping
        self.bind(width=self._update_label_width)
        self.add_widget(self.label)

    def _update_label_width(self, instance, value):
        self.label.text_size = (value - 20, None)  # Offset padding

class MainWindow(BoxLayout):
    """Root Layout for Supervised Chess AI Main Window with controls and move log tracking."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 10
        self.padding = 15

        # Initialize Chess AI Engine (MainWindow owns the AI instance)
        self.ai_engine = None
        self.ai_status = "AI Offline"
        self.move_history_list = [] # List storing all played moves in Standard Algebraic Notation (SAN)
        self.redo_stack = []        # Stack storing undone moves for redo capabilities
        self.promotion_popup = None # References the active modal promotion selection popup
        
        # Color state configuration (Human is default White)
        self.human_color = chess.WHITE
        self.ai_color = chess.BLACK
        
        try:
            from src.inference import ChessInference
            # Expose and initialize the single AI engine instance
            self.ai_engine = ChessInference()
            self.ai_status = "AI Ready"
            print("AI Engine successfully loaded and initialized (AI Ready).")
        except Exception as e:
            self.ai_status = f"AI Error: {e}"
            print(f"Warning: AI Engine failed to initialize: {e}")

        # 1. Header (Centered, Professional Title)
        header = Label(
            text="Supervised Chess AI",
            font_size='24sp',
            size_hint_y=None,
            height=50,
            bold=True
        )
        self.add_widget(header)

        # 2. Middle Content Area (Chess Board + Side Panel)
        content_area = BoxLayout(
            orientation='horizontal',
            spacing=15,
            size_hint_y=1.0  # Occupy remaining vertical space
        )
        
        # Left side: Chess Board Area
        self.chess_board = ChessBoard(
            on_move_executed_callback=self.on_move_executed_handler, 
            on_promotion_required_callback=self.show_promotion_dialog,
            size_hint_x=0.7
        )
        content_area.add_widget(self.chess_board)

        # Right side: Side Panel with game controls and move log
        side_panel = BoxLayout(
            orientation='vertical',
            spacing=10,
            size_hint_x=0.3,
            padding=10
        )
        
        # Section title
        side_panel.add_widget(Label(
            text="[ Game Controls & Info ]",
            font_size='16sp',
            bold=True,
            size_hint_y=None,
            height=30
        ))
        
        # Scrollable Move History panel
        side_panel.add_widget(Label(
            text="Move History",
            font_size='14sp',
            bold=True,
            size_hint_y=None,
            height=20
        ))
        self.history_scroll = ScrollableLabel(size_hint_y=0.4)
        side_panel.add_widget(self.history_scroll)
        
        # Display AI status
        side_panel.add_widget(Label(
            text=f"AI Status:\n{self.ai_status}",
            font_size='14sp',
            halign='center',
            valign='middle',
            bold=True,
            size_hint_y=None,
            height=40
        ))
        
        side_panel.add_widget(Label(
            text="AI Stats:\nModel: ChessMoveCNN\nValidation Loss: 4.0642\nTest Accuracy: 18.41%",
            font_size='14sp',
            halign='center',
            valign='middle'
        ))
        
        # Spinner side selection (affects next New Game start)
        side_panel.add_widget(Label(
            text="Select Player Side:",
            font_size='14sp',
            bold=True,
            size_hint_y=None,
            height=20
        ))
        self.side_spinner = Spinner(
            text="Play as White",
            values=("Play as White", "Play as Black"),
            size_hint_y=None,
            height=40,
            background_color=[0.1, 0.4, 0.6, 1.0] # Soft blue spinner
        )
        side_panel.add_widget(self.side_spinner)
        
        # Game reset button
        new_game_btn = Button(
            text="New Game",
            size_hint_y=None,
            height=45,
            bold=True,
            background_color=[0.2, 0.6, 0.3, 1.0] # Soft green button
        )
        new_game_btn.bind(on_press=lambda instance: self.start_new_game())
        side_panel.add_widget(new_game_btn)

        # Undo and Redo control row
        control_row = BoxLayout(
            orientation='horizontal',
            spacing=10,
            size_hint_y=None,
            height=45
        )
        
        self.undo_btn = Button(
            text="Undo",
            bold=True,
            background_color=[0.7, 0.2, 0.2, 1.0] # Soft red button
        )
        self.undo_btn.bind(on_press=lambda instance: self.undo_move())
        control_row.add_widget(self.undo_btn)
        
        self.redo_btn = Button(
            text="Redo",
            bold=True,
            background_color=[0.2, 0.4, 0.7, 1.0] # Soft blue button
        )
        self.redo_btn.bind(on_press=lambda instance: self.redo_move())
        control_row.add_widget(self.redo_btn)
        
        side_panel.add_widget(control_row)
        
        content_area.add_widget(side_panel)
        self.add_widget(content_area)

        # 3. Status Bar
        self.status_bar = Label(
            text="White to Move",
            font_size='14sp',
            size_hint_y=None,
            height=30,
            halign='left',
            valign='middle'
        )
        # Bind size for text alignment to work properly in Kivy
        self.status_bar.bind(size=self._align_status_bar_text)
        self.add_widget(self.status_bar)

        # 4. Load the starting position
        self.start_new_game()

    def set_player_side(self):
        """Sets the player and AI colors based on the spinner's active choice."""
        if self.side_spinner.text == "Play as White":
            self.human_color = chess.WHITE
            self.ai_color = chess.BLACK
        else:
            self.human_color = chess.BLACK
            self.ai_color = chess.WHITE

    def start_new_game(self):
        """Begins a fresh chess match respecting side selection configuration."""
        # Close any active promotion popups
        if self.promotion_popup:
            self.promotion_popup.dismiss()
            self.promotion_popup = None

        # 1. Update player and AI colors
        self.set_player_side()

        # 2. Reset board and history logs
        self.chess_board.reset_game()
        self.clear_history()
        self.clear_redo_stack()
        
        # 3. Lock board click interactions if it is currently the AI's turn
        self.chess_board.disable_interaction = not self.is_human_turn()
        self.update_game_status()
        self.update_button_states()

        # 4. If AI plays first (AI is White), immediately trigger its turn
        if self.is_ai_turn():
            self.execute_ai_move()

    def on_move_executed_handler(self, move: chess.Move, san_str: str):
        """Called automatically after a human move is completed on the board. Coordinates history and AI."""
        # A new move has been made; clear the redo stack
        self.clear_redo_stack()

        # 1. Record move to SAN log
        self.add_move_to_history(san_str)
        
        # 2. Lock board click interactions during turn switches
        self.chess_board.disable_interaction = not self.is_human_turn()
        self.update_game_status()
        
        # 3. Check if the game has ended
        if self.is_game_over():
            self.update_button_states()
            return
            
        # 4. Check if it is the AI's turn (AI is Black, human is White)
        if self.is_ai_turn():
            self.execute_ai_move()
        else:
            self.update_button_states()

    def execute_ai_move(self):
        """Triggers the Chess AI engine to predict and play Black's move."""
        if self.ai_engine is None:
            print("AI Engine not loaded. Continuing in Human-vs-Human mode.")
            self.chess_board.disable_interaction = False
            self.update_button_states()
            return

        # Disable user interactions on board during calculation
        self.chess_board.disable_interaction = True
        
        # Display thinking status
        player_side = "Playing as White" if self.human_color == chess.WHITE else "Playing as Black"
        self.status_bar.text = f"AI Thinking... | {player_side} | {self.ai_status}"
        
        try:
            board = self.chess_board.chess_board_obj
            # Call predict_best_move from ChessInference (runs model prediction pipeline)
            prediction = self.ai_engine.predict_best_move(board.fen())
            
            # Validate prediction move
            move = prediction.move
            if move is not None and move in board.legal_moves:
                # Generate SAN string *before* pushing onto the board
                san_str = board.san(move)
                # Push AI move to board
                board.push(move)
                # Redraw positions using standard layout update
                self.chess_board.load_position(board)
                # Record move to SAN log
                self.add_move_to_history(san_str)
                print(f"AI Move Executed: {prediction.uci} (Score: {prediction.logit:.4f})")
            else:
                err_msg = f"AI predicted illegal/None move: {prediction.uci if prediction else 'None'}"
                print(f"Error: {err_msg}")
                self.ai_status = "AI Error: Illegal move"
        except Exception as e:
            err_msg = f"AI inference error: {e}"
            print(f"Error: {err_msg}")
            self.ai_status = f"AI Error: Prediction failed"
            
        # Re-enable user interaction if it becomes the Human's turn
        self.chess_board.disable_interaction = not self.is_human_turn()
        
        # Update final game status and button states
        self.update_game_status()
        self.update_button_states()

    def show_promotion_dialog(self, from_square: int, to_square: int):
        """Displays a modal popup allowing the human to choose a promotion piece."""
        main_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Options grid containing buttons for Queen, Rook, Bishop, Knight
        choices_grid = GridLayout(cols=2, spacing=8, size_hint_y=0.7)
        options = [
            ("Queen", chess.QUEEN),
            ("Rook", chess.ROOK),
            ("Bishop", chess.BISHOP),
            ("Knight", chess.KNIGHT)
        ]
        
        for name, piece_type in options:
            btn = Button(text=name, font_size='16sp', bold=True)
            # Bind choice selection to complete the promotion
            btn.bind(on_release=lambda btn_instance, pt=piece_type: self.complete_promotion(from_square, to_square, pt))
            choices_grid.add_widget(btn)
            
        main_layout.add_widget(choices_grid)
        
        # Cancel option to cancel selection safely
        cancel_btn = Button(text="Cancel", font_size='14sp', size_hint_y=0.3, bold=True, background_color=[0.7, 0.2, 0.2, 1.0])
        cancel_btn.bind(on_release=lambda instance: self.cancel_promotion())
        main_layout.add_widget(cancel_btn)
        
        # Create and open the Popup
        self.promotion_popup = Popup(
            title="Pawn Promotion Select",
            content=main_layout,
            size_hint=(None, None),
            size=(320, 240),
            auto_dismiss=False  # Block board clicks until dismissed
        )
        self.promotion_popup.open()

    def complete_promotion(self, from_square: int, to_square: int, piece_type: int):
        """Executes the promotion move backend push, closes the dialog, and updates the game loop."""
        # 1. Close and cleanup popup
        if self.promotion_popup:
            self.promotion_popup.dismiss()
            self.promotion_popup = None
            
        board = self.chess_board.chess_board_obj
        if board is None:
            return
            
        # 2. Construct move with selected promotion piece
        move = chess.Move(from_square, to_square, promotion=piece_type)
        
        # 3. Push and execute move
        if move in board.legal_moves:
            # Generate SAN string *before* pushing onto the board
            san_str = board.san(move)
            
            # Clear redo stack
            self.clear_redo_stack()
            
            # Push move
            board.push(move)
            
            # Redraw board positions
            self.chess_board.load_position(board)
            
            # Record move to SAN log
            self.add_move_to_history(san_str)
            
            # Update status
            self.update_game_status()
            
            # 4. Handle turn switches
            self.chess_board.disable_interaction = not self.is_human_turn()
            
            if self.is_game_over():
                self.update_button_states()
                return
                
            if self.is_ai_turn():
                self.execute_ai_move()
            else:
                self.update_button_states()
        else:
            # Re-enable interaction if somehow illegal
            self.chess_board.disable_interaction = not self.is_human_turn()
            self.update_button_states()

    def cancel_promotion(self):
        """Cancels the active promotion request, clears selection/highlights, and closes the dialog."""
        if self.promotion_popup:
            self.promotion_popup.dismiss()
            self.promotion_popup = None
            
        # Re-enable standard interaction and clear highlights
        self.chess_board.clear_selection_and_highlights()
        self.chess_board.disable_interaction = not self.is_human_turn()
        self.update_button_states()
        print("Promotion cancelled.")

    def add_move_to_history(self, san_str: str):
        """Adds a new move to the PGN log list and triggers panel updates."""
        self.move_history_list.append(san_str)
        self.refresh_history_panel()

    def clear_history(self):
        """Clears all move lists and updates log panels."""
        self.move_history_list = []
        self.refresh_history_panel()

    def refresh_history_panel(self):
        """Draws the scrollable logs with aligned columns: 1. e4 e5."""
        log_lines = []
        for idx in range(0, len(self.move_history_list), 2):
            move_num = (idx // 2) + 1
            white_move = self.move_history_list[idx]
            
            if idx + 1 < len(self.move_history_list):
                black_move = self.move_history_list[idx + 1]
                log_lines.append(f"{move_num:2d}.  {white_move:<8}  {black_move}")
            else:
                log_lines.append(f"{move_num:2d}.  {white_move:<8}")
                
        self.history_scroll.label.text = "\n".join(log_lines)
        # Scroll automatically to the bottom
        self.history_scroll.scroll_y = 0.0

    def undo_move(self):
        """Undoes the latest move(s) and refreshes the GUI."""
        if not self.can_undo():
            return
            
        board = self.chess_board.chess_board_obj
        if board is None:
            return
            
        # Lock visual interaction check
        self.chess_board.clear_selection_and_highlights()
        
        if self.ai_engine is not None:
            # Human vs AI: pop 2 moves (AI response, then human move)
            m2 = board.pop() # AI move
            m1 = board.pop() # Human move
            self.redo_stack.append(m2)
            self.redo_stack.append(m1)
            # Remove 2 entries from SAN history log
            if len(self.move_history_list) >= 2:
                self.move_history_list.pop()
                self.move_history_list.pop()
        else:
            # Human vs Human: pop 1 move
            m1 = board.pop()
            self.redo_stack.append(m1)
            if self.move_history_list:
                self.move_history_list.pop()
                
        # Re-render board and refresh history displays
        self.chess_board.load_position(board)
        self.refresh_history_panel()
        self.chess_board.disable_interaction = not self.is_human_turn()
        self.update_game_status()
        self.update_button_states()
        print("Undo executed successfully.")

    def redo_move(self):
        """Redoes the undone move(s) and refreshes the GUI."""
        if not self.can_redo():
            return
            
        board = self.chess_board.chess_board_obj
        if board is None:
            return
            
        self.chess_board.clear_selection_and_highlights()
        
        if self.ai_engine is not None:
            # Human vs AI: pop 2 moves (Human move first, then AI move)
            m1 = self.redo_stack.pop() # Human move
            m2 = self.redo_stack.pop() # AI move
            
            # Generate SAN and push human move
            san_1 = board.san(m1)
            board.push(m1)
            self.move_history_list.append(san_1)
            
            # Generate SAN and push AI move
            san_2 = board.san(m2)
            board.push(m2)
            self.move_history_list.append(san_2)
        else:
            # Human vs Human: pop 1 move
            m1 = self.redo_stack.pop()
            san_1 = board.san(m1)
            board.push(m1)
            self.move_history_list.append(san_1)
            
        # Re-render board and refresh displays
        self.chess_board.load_position(board)
        self.refresh_history_panel()
        self.chess_board.disable_interaction = not self.is_human_turn()
        self.update_game_status()
        self.update_button_states()
        print("Redo executed successfully.")

    def can_undo(self) -> bool:
        """Returns True if the board state allows an undo action."""
        board = self.chess_board.chess_board_obj
        if board is None:
            return False
            
        if self.ai_engine is not None:
            return len(board.move_stack) >= 2
        else:
            return len(board.move_stack) >= 1

    def can_redo(self) -> bool:
        """Returns True if the redo stack contains moves that can be reapplied."""
        if self.ai_engine is not None:
            return len(self.redo_stack) >= 2
        else:
            return len(self.redo_stack) >= 1

    def clear_redo_stack(self):
        """Clears the redo stack and updates button states."""
        self.redo_stack = []
        self.update_button_states()

    def update_button_states(self):
        """Enables or disables Undo/Redo buttons based on availability of moves."""
        self.undo_btn.disabled = not self.can_undo()
        self.redo_btn.disabled = not self.can_redo()

    def is_human_turn(self) -> bool:
        """Returns True if the current turn belongs to the human player."""
        board = self.chess_board.chess_board_obj
        if board is None or board.is_game_over():
            return False
        return board.turn == self.human_color

    def is_ai_turn(self) -> bool:
        """Returns True if the current turn belongs to the AI engine."""
        board = self.chess_board.chess_board_obj
        if board is None or board.is_game_over():
            return False
        return board.turn == self.ai_color

    def update_game_status(self):
        """Checks the backend python-chess board object and updates status bar text."""
        board = self.chess_board.chess_board_obj
        if board is None:
            self.status_bar.text = f"Status: Ready | {self.ai_status}"
            return
            
        player_side = "Playing as White" if self.human_color == chess.WHITE else "Playing as Black"
        
        # Check game-ending states using python-chess APIs
        if board.is_game_over():
            if board.is_checkmate():
                winner = "Black" if board.turn == chess.WHITE else "White"
                status_text = f"Checkmate — {winner} Wins"
            elif board.is_stalemate():
                status_text = "Draw — Stalemate"
            elif board.is_insufficient_material():
                status_text = "Draw — Insufficient Material"
            elif board.is_threefold_repetition():
                status_text = "Draw — Threefold Repetition"
            elif board.is_fifty_moves():
                status_text = "Draw — Fifty-Move Rule"
            else:
                status_text = "Draw — Game Over"
            self.status_bar.text = f"{status_text} | {player_side} | {self.ai_status}"
            return
            
        # Check active play turn states
        if board.turn == chess.WHITE:
            # White's turn to move
            if board.move_stack:
                if self.human_color == chess.WHITE:
                    turn_str = f"White to Move — Black (AI) Played: {board.move_stack[-1].uci()}"
                else:
                    turn_str = f"White to Move — Black (Human) Played: {board.move_stack[-1].uci()}"
            else:
                turn_str = "White to Move"
        else:
            # Black's turn to move
            if board.move_stack:
                if self.human_color == chess.BLACK:
                    turn_str = f"Black to Move — White (AI) Played: {board.move_stack[-1].uci()}"
                else:
                    turn_str = f"Black to Move — White (Human) Played: {board.move_stack[-1].uci()}"
            else:
                turn_str = "Black to Move"
            
        if board.is_check():
            status_text = f"{turn_str} — Check"
        else:
            status_text = turn_str
            
        self.status_bar.text = f"{status_text} | {player_side} | {self.ai_status}"

    def reset_game(self):
        """Fallback method (delegates to start_new_game for clean state resets)."""
        self.start_new_game()

    def _align_status_bar_text(self, instance, value):
        instance.text_size = value
