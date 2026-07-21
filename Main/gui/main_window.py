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
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from chess_board import ChessBoard
from chess_piece import ChessPiece
from settings_manager import SettingsManager
from theme_manager import ThemeManager

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
        # 1. Initialize persistent SettingsManager
        self.settings_manager = SettingsManager()
        
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
        self.settings_popup = None  # References the active settings popup dialog
        self.is_animating = False   # Flag to track active piece animation loops
        
        # Color state configuration (Human is default White)
        self.human_color = chess.WHITE
        self.ai_color = chess.BLACK
        
        # Setup application background color
        with self.canvas.before:
            self.bg_color = Color(0.1, 0.1, 0.1, 1.0)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        try:
            from src.inference import ChessInference
            # Expose and initialize the single AI engine instance
            self.ai_engine = ChessInference()
            self.set_ai_status("AI Ready")
            from kivy.logger import Logger
            Logger.info("SupervisedChessAI: AI Engine successfully loaded and initialized (AI Ready).")
        except Exception as e:
            self.set_ai_status(f"AI Error: {e}")
            from kivy.logger import Logger
            Logger.error(f"SupervisedChessAI: AI Engine failed to initialize: {e}")

        # 2. Header (Centered, Professional Title)
        header = Label(
            text="Supervised Chess AI",
            font_size='24sp',
            size_hint_y=None,
            height=50,
            bold=True
        )
        self.add_widget(header)

        # 3. Middle Content Area (Chess Board + Side Panel)
        content_area = BoxLayout(
            orientation='horizontal',
            spacing=15,
            size_hint_y=1.0  # Occupy remaining vertical space
        )
        
        # Left side: Chess Board Area
        self.chess_board = ChessBoard(
            on_move_executed_callback=self.on_move_executed_handler, 
            on_promotion_required_callback=self.show_promotion_dialog,
            on_move_started_callback=self.on_move_started_handler,
            settings_manager=self.settings_manager,
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
        
        # Captured Pieces Section
        side_panel.add_widget(Label(
            text="Captured Pieces",
            font_size='14sp',
            bold=True,
            size_hint_y=None,
            height=20
        ))
        
        # White's captures container (Black pieces captured by White)
        self.white_captured_container = BoxLayout(
            orientation='horizontal',
            spacing=2,
            size_hint_y=None,
            height=30
        )
        self.white_captured_label = Label(
            text="White: ",
            font_size='12sp',
            bold=True,
            size_hint_x=None,
            width=60,
            halign='left',
            valign='middle'
        )
        self.white_captured_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        self.white_captured_pieces_box = BoxLayout(orientation='horizontal', spacing=1)
        self.white_captured_container.add_widget(self.white_captured_label)
        self.white_captured_container.add_widget(self.white_captured_pieces_box)
        side_panel.add_widget(self.white_captured_container)
        
        # Black's captures container (White pieces captured by Black)
        self.black_captured_container = BoxLayout(
            orientation='horizontal',
            spacing=2,
            size_hint_y=None,
            height=30
        )
        self.black_captured_label = Label(
            text="Black: ",
            font_size='12sp',
            bold=True,
            size_hint_x=None,
            width=60,
            halign='left',
            valign='middle'
        )
        self.black_captured_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        self.black_captured_pieces_box = BoxLayout(orientation='horizontal', spacing=1)
        self.black_captured_container.add_widget(self.black_captured_label)
        self.black_captured_container.add_widget(self.black_captured_pieces_box)
        side_panel.add_widget(self.black_captured_container)
        
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
        self.ai_status_lbl = Label(
            text=f"AI Status:\n{self.ai_status}",
            font_size='14sp',
            halign='center',
            valign='middle',
            bold=True,
            size_hint_y=None,
            height=40
        )
        side_panel.add_widget(self.ai_status_lbl)
        
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
        self.new_game_btn = Button(
            text="New Game",
            size_hint_y=None,
            height=45,
            bold=True,
            background_color=[0.2, 0.6, 0.3, 1.0] # Soft green button
        )
        self.new_game_btn.bind(on_press=lambda instance: self.start_new_game())
        side_panel.add_widget(self.new_game_btn)

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

        # Settings Configuration Button
        self.settings_btn = Button(
            text="Settings",
            size_hint_y=None,
            height=45,
            bold=True,
            background_color=[0.4, 0.4, 0.4, 1.0] # Soft gray button
        )
        self.settings_btn.bind(on_press=lambda instance: self.show_settings_dialog())
        side_panel.add_widget(self.settings_btn)
        
        content_area.add_widget(side_panel)
        self.add_widget(content_area)

        # 4. Status Bar
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

        # 5. Load settings and start
        self.apply_app_theme(self.settings_manager.get("app_theme"))
        self.start_new_game()

    def _update_bg(self, instance, value):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def set_player_side(self):
        """Sets the player and AI colors based on the spinner's active choice."""
        if self.side_spinner.text == "Play as White":
            self.human_color = chess.WHITE
            self.ai_color = chess.BLACK
        else:
            self.human_color = chess.BLACK
            self.ai_color = chess.WHITE

    def is_game_over(self):
        """Checks if the current game has ended (checkmate, stalemate, draw, etc)."""
        board = self.chess_board.chess_board_obj
        if board is None:
            return False

        if board.is_game_over():
            if board.is_checkmate():
                winner = "Black" if board.turn == chess.WHITE else "White"
                self.status_bar.text = f"Checkmate! {winner} wins."
            elif board.is_stalemate():
                self.status_bar.text = "Draw by stalemate."
            elif board.is_insufficient_material():
                self.status_bar.text = "Draw by insufficient material."
            else:
                self.status_bar.text = "Game Over — Draw."
            self.chess_board.disable_interaction = True
            return True

        return False

    def set_ai_status(self, status_str):
        """Sets the AI status string and dynamically updates the visual status label."""
        self.ai_status = status_str
        if hasattr(self, 'ai_status_lbl'):
            self.ai_status_lbl.text = f"AI Status:\n{self.ai_status}"

    def start_new_game(self):
        """Begins a fresh chess match respecting side selection configuration."""
        if self.is_animating:
            return  # Prevent resetting during animation

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
        
        # 3. Apply themes automatically from SettingsManager
        self.chess_board.apply_board_theme(self.settings_manager.get("board_theme"))
        
        # 4. Lock board click interactions if it is currently the AI's turn
        self.chess_board.disable_interaction = not self.is_human_turn()
        self.update_game_status()
        self.update_button_states()

        # 5. If AI plays first (AI is White), immediately trigger its turn
        if self.is_ai_turn():
            self.execute_ai_move()

    def on_move_started_handler(self):
        """Callback invoked when a board movement animation begins. Disables all buttons."""
        self.is_animating = True
        self.update_button_states()

    def on_move_executed_handler(self, move: chess.Move, san_str: str):
        """Called automatically after a human move is completed on the board. Coordinates history and AI."""
        # A new move has been made; clear the redo stack
        self.clear_redo_stack()

        # 1. Record move to SAN log
        self.add_move_to_history(san_str)
        
        # 2. Update board model state
        board = self.chess_board.chess_board_obj
        board.push(move)
        
        # Redraw board positions deterministically (clears animated instances)
        self.chess_board.load_position(board)
        
        # 3. Reset animation status
        self.is_animating = False
        
        # 4. Lock board click interactions during turn switches
        self.chess_board.disable_interaction = not self.is_human_turn()
        self.update_game_status()
        
        # 5. Check if the game has ended
        if self.is_game_over():
            self.update_button_states()
            return
            
        # 6. Check if it is the AI's turn (AI is Black, human is White)
        if self.is_ai_turn():
            delay_ms = self.settings_manager.get("ai_thinking_delay")
            if delay_ms > 0:
                Clock.schedule_once(lambda dt: self.execute_ai_move(), delay_ms / 1000.0)
            else:
                self.execute_ai_move()
        else:
            self.update_button_states()

    def execute_ai_move(self):
        """Triggers the Chess AI engine to predict and play Black's move."""
        if not self.settings_manager.get("ai_enabled") or self.ai_engine is None:
            print("AI Engine not enabled or loaded. Continuing in Human-vs-Human mode.")
            self.chess_board.disable_interaction = False
            self.is_animating = False
            self.update_button_states()
            return

        # Disable user interactions on board during calculation
        self.chess_board.disable_interaction = True
        self.is_animating = True
        self.update_button_states()
        
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
                # Trigger AI move animation, defer push/redraw on complete callback
                self.chess_board.animate_move(move, lambda: self.finish_ai_move_execution(move, prediction))
            else:
                err_msg = f"AI predicted illegal/None move: {prediction.uci if prediction else 'None'}"
                print(f"Error: {err_msg}")
                self.set_ai_status("AI Error: Illegal move")
                self.is_animating = False
                self.chess_board.disable_interaction = not self.is_human_turn()
                self.update_game_status()
                self.update_button_states()
        except Exception as e:
            err_msg = f"AI inference error: {e}"
            print(f"Error: {err_msg}")
            self.set_ai_status(f"AI Error: Prediction failed")
            self.is_animating = False
            self.chess_board.disable_interaction = not self.is_human_turn()
            self.update_game_status()
            self.update_button_states()

    def finish_ai_move_execution(self, move: chess.Move, prediction):
        """Pushes AI move on backend, refreshes positions, logs SAN, and restores locks."""
        board = self.chess_board.chess_board_obj
        if board is not None:
            # Generate SAN string *before* pushing onto the board
            san_str = board.san(move)
            # Push AI move to board
            board.push(move)
            # Redraw positions using standard layout update
            self.chess_board.load_position(board)
            # Record move to SAN log
            self.add_move_to_history(san_str)
            print(f"AI Move Executed: {prediction.uci} (Score: {prediction.logit:.4f})")
            
        # Reset animation flag and restore locks
        self.is_animating = False
        self.chess_board.disable_interaction = not self.is_human_turn()
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
        
        # 3. Trigger move started callback to lock interaction
        self.on_move_started_handler()
        
        # 4. Trigger promotion slide animation
        self.chess_board.animate_move(move, lambda: self.finish_promotion_execution(move))

    def finish_promotion_execution(self, move: chess.Move):
        """Completes the promotion move pushing, redraws board, and shifts turns."""
        board = self.chess_board.chess_board_obj
        if board is not None:
            san_str = board.san(move)
            self.clear_redo_stack()
            board.push(move)
            self.chess_board.load_position(board)
            self.add_move_to_history(san_str)
            self.update_game_status()
            
        self.is_animating = False
        self.chess_board.disable_interaction = not self.is_human_turn()
        
        if self.is_game_over():
            self.update_button_states()
            return
            
        if self.is_ai_turn():
            delay_ms = self.settings_manager.get("ai_thinking_delay")
            if delay_ms > 0:
                Clock.schedule_once(lambda dt: self.execute_ai_move(), delay_ms / 1000.0)
            else:
                self.execute_ai_move()
        else:
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
        
        # Scroll automatically to the bottom if auto-scroll setting is enabled
        if self.settings_manager.get("auto_scroll_history"):
            self.history_scroll.scroll_y = 0.0

    def undo_move(self):
        """Undoes the latest move(s) and refreshes the GUI."""
        if not self.can_undo() or self.is_animating:
            return
            
        board = self.chess_board.chess_board_obj
        if board is None:
            return
            
        # Lock visual interaction check
        self.chess_board.clear_selection_and_highlights()
        
        if self.settings_manager.get("ai_enabled") and self.ai_engine is not None:
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
            # Human vs Human (or AI disabled): pop 1 move
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
        if not self.can_redo() or self.is_animating:
            return
            
        board = self.chess_board.chess_board_obj
        if board is None:
            return
            
        self.chess_board.clear_selection_and_highlights()
        
        if self.settings_manager.get("ai_enabled") and self.ai_engine is not None:
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
        if self.is_animating:
            return False
        board = self.chess_board.chess_board_obj
        if board is None:
            return False
            
        if self.settings_manager.get("ai_enabled") and self.ai_engine is not None:
            return len(board.move_stack) >= 2
        else:
            return len(board.move_stack) >= 1

    def can_redo(self) -> bool:
        """Returns True if the redo stack contains moves that can be reapplied."""
        if self.is_animating:
            return False
        if self.settings_manager.get("ai_enabled") and self.ai_engine is not None:
            return len(self.redo_stack) >= 2
        else:
            return len(self.redo_stack) >= 1

    def clear_redo_stack(self):
        """Clears the redo stack and updates button states."""
        self.redo_stack = []
        self.update_button_states()

    def update_button_states(self):
        """Enables or disables Undo/Redo/New Game buttons based on state."""
        # Disable all controls during active movement animation
        if self.is_animating:
            self.undo_btn.disabled = True
            self.redo_btn.disabled = True
            self.new_game_btn.disabled = True
            self.settings_btn.disabled = True
        else:
            self.undo_btn.disabled = not self.can_undo()
            self.redo_btn.disabled = not self.can_redo()
            self.new_game_btn.disabled = False
            self.settings_btn.disabled = False

    def is_human_turn(self) -> bool:
        """Returns True if the current turn belongs to the human player."""
        board = self.chess_board.chess_board_obj
        if board is None or board.is_game_over():
            return False
        return board.turn == self.human_color

    def is_ai_turn(self) -> bool:
        """Returns True if the current turn belongs to the AI engine."""
        if not self.settings_manager.get("ai_enabled") or self.ai_engine is None:
            return False
        board = self.chess_board.chess_board_obj
        if board is None or board.is_game_over():
            return False
        return board.turn == self.ai_color

    def calculate_captured_pieces(self):
        """Calculates captured pieces for both sides by comparing current board to starting counts."""
        board = self.chess_board.chess_board_obj
        if board is None:
            return {}
            
        # Standard starting pieces counts
        starting = {
            chess.WHITE: {chess.PAWN: 8, chess.KNIGHT: 2, chess.BISHOP: 2, chess.ROOK: 2, chess.QUEEN: 1},
            chess.BLACK: {chess.PAWN: 8, chess.KNIGHT: 2, chess.BISHOP: 2, chess.ROOK: 2, chess.QUEEN: 1}
        }
        
        # Count remaining pieces on the board
        remaining = {
            chess.WHITE: {chess.PAWN: 0, chess.KNIGHT: 0, chess.BISHOP: 0, chess.ROOK: 0, chess.QUEEN: 0},
            chess.BLACK: {chess.PAWN: 0, chess.KNIGHT: 0, chess.BISHOP: 0, chess.ROOK: 0, chess.QUEEN: 0}
        }
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is not None and piece.piece_type != chess.KING:
                remaining[piece.color][piece.piece_type] += 1
                
        # Calculate captured pieces counts (derived directly from current state)
        captured = {
            chess.WHITE: {}, # White pieces captured (by Black)
            chess.BLACK: {}  # Black pieces captured (by White)
        }
        
        for color in [chess.WHITE, chess.BLACK]:
            for pt in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]:
                count = starting[color][pt] - remaining[color][pt]
                if count > 0:
                    captured[color][pt] = count
                    
        return captured

    def calculate_material_balance(self) -> int:
        """Calculates the current material balance from White's perspective."""
        board = self.chess_board.chess_board_obj
        if board is None:
            return 0
            
        values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9
        }
        
        white_total = 0
        black_total = 0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is not None:
                val = values.get(piece.piece_type, 0)
                if piece.color == chess.WHITE:
                    white_total += val
                else:
                    black_total += val
                    
        return white_total - black_total

    def refresh_captured_pieces(self):
        """Re-calculates captured pieces and material balance from current board, then redraws GUI panels."""
        # 1. Clear old captured piece widgets
        self.white_captured_pieces_box.clear_widgets()
        self.black_captured_pieces_box.clear_widgets()
        
        # 2. Compute captured counts directly from current board state
        captured = self.calculate_captured_pieces()
        
        # Mapping from piece type ints to string names
        piece_type_map = {
            chess.QUEEN: 'queen',
            chess.ROOK: 'rook',
            chess.BISHOP: 'bishop',
            chess.KNIGHT: 'knight',
            chess.PAWN: 'pawn'
        }
        
        # Resolve piece rendering display format from settings
        piece_display_setting = "Unicode"
        use_images = True
        if self.settings_manager:
            piece_display_setting = self.settings_manager.get("piece_display")
            use_images = (piece_display_setting != "Unicode")
        
        # 3. Add Black pieces captured by White (White's captures panel)
        black_captured_dict = captured.get(chess.BLACK, {})
        for pt in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]:
            count = black_captured_dict.get(pt, 0)
            for _ in range(count):
                piece_widget = ChessPiece(
                    piece_type=piece_type_map[pt], 
                    color='b', 
                    use_images=use_images, 
                    piece_display_setting=piece_display_setting,
                    size_hint=(None, 1), 
                    width=18
                )
                self.white_captured_pieces_box.add_widget(piece_widget)
                
        # 4. Add White pieces captured by Black (Black's captures panel)
        white_captured_dict = captured.get(chess.WHITE, {})
        for pt in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]:
            count = white_captured_dict.get(pt, 0)
            for _ in range(count):
                piece_widget = ChessPiece(
                    piece_type=piece_type_map[pt], 
                    color='w', 
                    use_images=use_images, 
                    piece_display_setting=piece_display_setting,
                    size_hint=(None, 1), 
                    width=18
                )
                self.black_captured_pieces_box.add_widget(piece_widget)
                
        # 5. Update material balance indicators
        balance = self.calculate_material_balance()
        if balance > 0:
            self.white_captured_label.text = f"White: +{balance}"
            self.black_captured_label.text = "Black: "
        elif balance < 0:
            self.white_captured_label.text = "White: "
            self.black_captured_label.text = f"Black: +{abs(balance)}"
        else:
            self.white_captured_label.text = "White: "
            self.black_captured_label.text = "Black: "

    def show_settings_dialog(self):
        """Displays a modal popup dialog containing all settings categories."""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        grid = GridLayout(cols=2, spacing=10, size_hint_y=0.8)
        
        def add_setting_spinner(label_text, key, values, display_map=None):
            grid.add_widget(Label(text=label_text, halign='left', size_hint_x=0.6))
            
            current_val = self.settings_manager.get(key)
            if display_map:
                text_val = [k for k, v in display_map.items() if v == current_val][0]
            else:
                text_val = str(current_val)
                
            spinner = Spinner(
                text=text_val,
                values=list(display_map.keys()) if display_map else [str(v) for v in values],
                size_hint_x=0.4
            )
            
            def on_choice(spinner_inst, choice_text):
                if display_map:
                    new_val = display_map[choice_text]
                else:
                    default_type = type(self.settings_manager.DEFAULT_SETTINGS[key])
                    new_val = default_type(choice_text)
                    
                self.settings_manager.set(key, new_val)
                self.apply_setting(key, new_val)
                
            spinner.bind(text=on_choice)
            grid.add_widget(spinner)

        # Map display labels to backend config values
        on_off_map = {"On": True, "Off": False}
        delay_map = {"0 ms": 0, "250 ms": 250, "500 ms": 500, "1000 ms": 1000}
        
        add_setting_spinner("App Theme:", "app_theme", ["Dark", "Light"])
        add_setting_spinner("Board Theme:", "board_theme", ThemeManager.get_available_themes())
        add_setting_spinner("Piece Display:", "piece_display", ThemeManager.get_available_piece_sets())
        add_setting_spinner("Animation:", "animation_enabled", [True, False], on_off_map)
        add_setting_spinner("Animation Speed:", "animation_speed", ["Slow", "Normal", "Fast"])
        add_setting_spinner("AI Enabled:", "ai_enabled", [True, False], on_off_map)
        add_setting_spinner("AI Thinking Delay:", "ai_thinking_delay", [0, 250, 500, 1000], delay_map)
        add_setting_spinner("Auto-scroll History:", "auto_scroll_history", [True, False], on_off_map)
        
        content.add_widget(grid)
        
        # Close button
        close_btn = Button(text="Close", size_hint_y=0.2, bold=True)
        self.settings_popup = Popup(
            title="Settings Configuration",
            content=content,
            size_hint=(None, None),
            size=(400, 420)
        )
        close_btn.bind(on_release=self.settings_popup.dismiss)
        content.add_widget(close_btn)
        
        self.settings_popup.open()

    def apply_setting(self, key, value):
        """Immediately applies setting updates to the visual and logical pipelines."""
        if key == "app_theme":
            self.apply_app_theme(value)
        elif key == "board_theme":
            self.chess_board.apply_board_theme(value)
        elif key == "piece_display":
            # Re-draw layout pieces to apply Image vs Unicode asset changes
            board = self.chess_board.chess_board_obj
            if board is not None:
                self.chess_board.load_position(board)
            # Re-draw captured piece widgets matching chosen display
            self.refresh_captured_pieces()
        elif key == "ai_enabled":
            # Update board interaction and button locks
            self.chess_board.disable_interaction = not self.is_human_turn()
            self.update_button_states()
            if self.is_ai_turn():
                self.execute_ai_move()

    def apply_app_theme(self, theme_name: str):
        """Recursively updates Kivy widgets colors matching Dark/Light application theme."""
        bg_rgb = [0.1, 0.1, 0.1, 1.0] if theme_name == "Dark" else [0.95, 0.95, 0.95, 1.0]
        text_color = [1.0, 1.0, 1.0, 1.0] if theme_name == "Dark" else [0.1, 0.1, 0.1, 1.0]
        
        # Update main window background color
        self.bg_color.rgba = bg_rgb
        
        # Recursive widget style updater
        def update_widget(w):
            if isinstance(w, Label):
                w.color = text_color
            for child in w.children:
                update_widget(child)
                
        update_widget(self)

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
            self.refresh_captured_pieces()
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
        self.refresh_captured_pieces()

    def _align_status_bar_text(self, instance, value):
        instance.text_size = value
