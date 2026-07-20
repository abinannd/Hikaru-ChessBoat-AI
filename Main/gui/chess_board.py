import sys
from pathlib import Path

# Resolve directories to allow direct execution
GUI_ROOT = Path(__file__).resolve().parent
if str(GUI_ROOT) not in sys.path:
    sys.path.insert(0, str(GUI_ROOT))

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle
from kivy.animation import Animation

# Import python-chess and our custom ChessPiece widget
import chess
from chess_piece import ChessPiece

# Color Theme Constants (Professional chess.com wood theme)
LIGHT_SQUARE_COLOR = [240/255, 217/255, 181/255, 1.0]      # #F0D9B5
DARK_SQUARE_COLOR = [181/255, 136/255, 99/255, 1.0]       # #B58863
HIGHLIGHT_COLOR = [186/255, 202/255, 43/255, 1.0]          # #BACA2B (Soft selection green)
LEGAL_HIGHLIGHT_COLOR = [72/255, 120/255, 209/255, 0.5]    # Semi-transparent blue overlay for legal destinations

class ChessSquare(BoxLayout):
    """An individual square on the chessboard."""

    def __init__(self, coordinate: str, is_dark: bool, **kwargs):
        super().__init__(**kwargs)
        self.coordinate = coordinate
        self.is_dark = is_dark
        self.square_color = DARK_SQUARE_COLOR if is_dark else LIGHT_SQUARE_COLOR
        self.is_selected = False
        self.is_legal_destination = False
        
        # Draw background color canvas instruction
        with self.canvas.before:
            self.canvas_color = Color(*self.square_color)
            self.rect = Rectangle(pos=self.pos, size=self.size)
            
        # Bind pos and size changes to update rectangle
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, instance, value):
        """Keep the background rectangle aligned with the widget's position and size."""
        self.rect.pos = self.pos
        self.rect.size = self.size

    def select(self):
        """Visually highlights the square as selected."""
        self.is_selected = True
        self.canvas_color.rgba = HIGHLIGHT_COLOR

    def deselect(self):
        """Restores the square's original color."""
        self.is_selected = False
        self.canvas_color.rgba = self.square_color

    def show_legal_move(self):
        """Visually highlights this square as a legal destination."""
        self.is_legal_destination = True
        self.canvas_color.rgba = LEGAL_HIGHLIGHT_COLOR

    def clear_legal_move(self):
        """Restores the square's original color (removes legal highlight)."""
        self.is_legal_destination = False
        self.canvas_color.rgba = self.square_color

class ChessBoard(FloatLayout):
    """Responsive 8x8 Chessboard Widget with Piece Animations."""

    def __init__(self, on_move_executed_callback=None, on_promotion_required_callback=None, on_move_started_callback=None, **kwargs):
        super().__init__(**kwargs)
        
        # Expose properties for piece placement, highlights, and game logic
        self.board_size = 8
        self.squares = {}              # Dictionary for coordinate-to-widget lookup (e.g. self.squares["e4"])
        self.square_list = []          # List of all ChessSquare widgets (exactly 64)
        self.selected_square = None     # References the currently selected ChessSquare, None if nothing selected
        self.highlighted_squares = []  # List of ChessSquare widgets currently highlighted as legal destinations
        self.chess_board_obj = None     # Holds the internal python-chess.Board() object (source of truth)
        self.on_move_executed = on_move_executed_callback # Callback fired when a move is successfully pushed
        self.on_promotion_required = on_promotion_required_callback # Callback fired when human pawn promotion is detected
        self.on_move_started = on_move_started_callback # Callback fired when a move animation starts
        self.disable_interaction = False # Flag to temporarily lock board clicks (e.g., during AI turns / animations)
        self.active_animations = 0     # Counter of concurrently running animations
        
        # 8x8 Grid layout for squares
        self.board_grid = GridLayout(cols=8, rows=8, size_hint=(None, None))
        
        # Generate 64 squares from top-left (a8) to bottom-right (h1)
        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        
        # Ranks run from 8 down to 1 (top to bottom)
        for rank_idx in range(7, -1, -1):
            rank_label = str(rank_idx + 1)
            # Files run from a to h (left to right)
            for file_idx in range(8):
                file_label = files[file_idx]
                coordinate = f"{file_label}{rank_label}"
                
                # Check square color (a1 is dark; file 0 + rank 0 = 0 (even) is dark)
                is_dark = (file_idx + rank_idx) % 2 == 0
                
                square_widget = ChessSquare(coordinate=coordinate, is_dark=is_dark)
                
                # Store references for lookup
                self.squares[coordinate] = square_widget
                self.square_list.append(square_widget)
                
                # Add to grid
                self.board_grid.add_widget(square_widget)
                
        # Add the board grid to this layout
        self.add_widget(self.board_grid)
        
        # Bind layout changes to dynamically resize and center the board
        self.bind(size=self._resize_board, pos=self._resize_board)

    def load_position(self, board: chess.Board):
        """Clears all existing pieces/highlights and loads the given python-chess board position."""
        # Save board reference as the source of truth
        self.chess_board_obj = board
        
        # Clear all active selections and highlights
        self.clear_selection_and_highlights()

        # 1. Clear existing pieces from all square widgets
        for square_widget in self.square_list:
            square_widget.clear_widgets()

        # 2. Map pieces from python-chess board representation to GUI coordinates
        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        
        # Mapping from piece types to string labels
        piece_type_map = {
            chess.PAWN: 'pawn',
            chess.KNIGHT: 'knight',
            chess.BISHOP: 'bishop',
            chess.ROOK: 'rook',
            chess.QUEEN: 'queen',
            chess.KING: 'king'
        }

        # Scan all 64 squares from python-chess mapping (0 to 63)
        for square_idx in range(64):
            piece = board.piece_at(square_idx)
            if piece is not None:
                # Resolve file and rank indices
                file_idx = chess.square_file(square_idx)
                rank_idx = chess.square_rank(square_idx)
                coordinate = f"{files[file_idx]}{rank_idx + 1}"
                
                if coordinate in self.squares:
                    piece_type = piece_type_map[piece.piece_type]
                    color = 'w' if piece.color == chess.WHITE else 'b'
                    
                    # Instantiate custom ChessPiece widget
                    piece_widget = ChessPiece(piece_type=piece_type, color=color)
                    
                    # Add to parent ChessSquare widget (automatically resizes and centers)
                    self.squares[coordinate].add_widget(piece_widget)

    def clear_selection_and_highlights(self):
        """Deselects the active square and clears all legal move highlights."""
        if self.selected_square is not None:
            self.selected_square.deselect()
            self.selected_square = None
            
        for square in self.highlighted_squares:
            square.clear_legal_move()
        self.highlighted_squares = []

    def handle_square_click(self, square: ChessSquare):
        """Coordinates selection changes and executes legal human moves."""
        # 1. Check if we clicked the currently selected square -> Deselect all
        if self.selected_square == square:
            self.clear_selection_and_highlights()
            return

        # 2. Check if we have a selected square AND the clicked square is a highlighted legal destination
        if self.selected_square is not None and square in self.highlighted_squares:
            # Clicked a legal move destination! Execute the move.
            from_square = chess.parse_square(self.selected_square.coordinate)
            to_square = chess.parse_square(square.coordinate)
            
            # Check if this move is a human pawn promotion (human pawns reaching 1st or 8th rank)
            piece = self.chess_board_obj.piece_at(from_square)
            is_promotion = False
            if piece is not None and piece.piece_type == chess.PAWN:
                to_rank = chess.square_rank(to_square)
                if (piece.color == chess.WHITE and to_rank == 7) or (piece.color == chess.BLACK and to_rank == 0):
                    is_promotion = True
            
            if is_promotion:
                # Trigger promotion dialog callback instead of auto-promoting to Queen
                if self.on_promotion_required:
                    self.disable_interaction = True
                    self.on_promotion_required(from_square, to_square)
                    return
            
            # Standard move execution (non-promotion)
            move = chess.Move(from_square, to_square)
            
            # Generate the SAN string *before* pushing onto the board
            san_str = self.chess_board_obj.san(move)
            
            # Trigger the animation first! Defer the actual push and history update
            if self.on_move_executed:
                if self.on_move_started:
                    self.on_move_started()
                self.animate_move(move, lambda: self.on_move_executed(move, san_str))
            return

        # 3. If we clicked an illegal square (or another piece), update selection normally
        self.clear_selection_and_highlights()
        self.selected_square = square
        self.selected_square.select()

        # 4. If the selected square is occupied, calculate and highlight legal moves
        if self.chess_board_obj is not None:
            square_idx = chess.parse_square(square.coordinate)
            piece = self.chess_board_obj.piece_at(square_idx)
            
            if piece is not None:
                files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
                
                # Fetch all legal moves starting from the selected square
                for move in self.chess_board_obj.legal_moves:
                    if move.from_square == square_idx:
                        dest_square_idx = move.to_square
                        
                        # Map destination square index back to coordinate string
                        dest_file = chess.square_file(dest_square_idx)
                        dest_rank = chess.square_rank(dest_square_idx)
                        dest_coordinate = f"{files[dest_file]}{dest_rank + 1}"
                        
                        if dest_coordinate in self.squares:
                            dest_square_widget = self.squares[dest_coordinate]
                            dest_square_widget.show_legal_move()
                            self.highlighted_squares.append(dest_square_widget)

    def animate_move(self, move: chess.Move, on_complete_callback):
        """Locates the moving piece(s) and animates them using Kivy Animation class."""
        self.disable_interaction = True
        
        # 1. Resolve source and destination coordinates
        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        from_coord = f"{files[chess.square_file(move.from_square)]}{chess.square_rank(move.from_square) + 1}"
        to_coord = f"{files[chess.square_file(move.to_square)]}{chess.square_rank(move.to_square) + 1}"
        
        start_square = self.squares.get(from_coord)
        dest_square = self.squares.get(to_coord)
        
        if start_square is None or dest_square is None:
            on_complete_callback()
            return
            
        # 2. Locate the ChessPiece child widget inside the starting square layout
        piece_widget = None
        for child in start_square.children:
            if isinstance(child, ChessPiece):
                piece_widget = child
                break
                
        if piece_widget is None:
            on_complete_callback()
            return

        # 3. Check for castling moves (castling animates both King and Rook)
        is_castling = self.chess_board_obj is not None and self.chess_board_obj.is_castling(move)
        self.active_animations = 0
        
        # Callback fired when an individual piece animation finishes
        def anim_callback(anim, widget):
            self.active_animations -= 1
            if self.active_animations == 0:
                on_complete_callback()

        if is_castling:
            # Determine Rook source and destination squares
            if move.to_square == chess.G1:     # White Kingside
                rook_from, rook_to = chess.H1, chess.F1
            elif move.to_square == chess.C1:   # White Queenside
                rook_from, rook_to = chess.A1, chess.D1
            elif move.to_square == chess.G8:   # Black Kingside
                rook_from, rook_to = chess.H8, chess.F8
            elif move.to_square == chess.C8:   # Black Queenside
                rook_from, rook_to = chess.A8, chess.D8
                
            rook_from_coord = f"{files[chess.square_file(rook_from)]}{chess.square_rank(rook_from) + 1}"
            rook_to_coord = f"{files[chess.square_file(rook_to)]}{chess.square_rank(rook_to) + 1}"
            
            rook_start = self.squares.get(rook_from_coord)
            rook_dest = self.squares.get(rook_to_coord)
            
            # Locate rook piece
            rook_widget = None
            if rook_start:
                for child in rook_start.children:
                    if isinstance(child, ChessPiece):
                        rook_widget = child
                        break
                        
            # Trigger both animations simultaneously
            self._animate_single_piece(piece_widget, start_square, dest_square, anim_callback)
            if rook_widget and rook_start and rook_dest:
                self._animate_single_piece(rook_widget, rook_start, rook_dest, anim_callback)
        else:
            # Normal moves (including captures and promotion translations)
            self._animate_single_piece(piece_widget, start_square, dest_square, anim_callback)

    def _animate_single_piece(self, piece_widget, start_square, dest_square, callback):
        """Temporarily detaches the piece widget and slides it smoothly on the top FloatLayout layer."""
        self.active_animations += 1
        
        # Capture absolute coordinates within the ChessBoard parent container
        start_pos = start_square.pos
        start_size = start_square.size
        dest_pos = dest_square.pos
        
        # Remove from the starting grid cell BoxLayout to bypass layout overrides during pos slide
        start_square.remove_widget(piece_widget)
        
        # Add directly to the top-level FloatLayout container (renders above the board)
        self.add_widget(piece_widget)
        piece_widget.size_hint = (None, None)
        piece_widget.size = start_size
        piece_widget.pos = start_pos
        
        # Animate smoothly from start to destination using Kivy Animation
        anim = Animation(pos=dest_pos, duration=0.2, transition='in_out_quad')
        anim.bind(on_complete=lambda a, w: self._cleanup_animated_piece(a, w, callback))
        anim.start(piece_widget)

    def _cleanup_animated_piece(self, anim, piece_widget, callback):
        """Removes the animated piece widget from the FloatLayout container and fires the callback."""
        self.remove_widget(piece_widget)
        callback(anim, piece_widget)

    def reset_game(self):
        """Resets the backend board to standard setup and redraws the starting position."""
        new_board = chess.Board()
        self.load_position(new_board)

    def on_touch_down(self, touch):
        """Intercepts touches to check for clicks. Blocks interaction if disabled or game is over."""
        # Only respond if the touch is within the bounds of this ChessBoard widget
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
            
        # Completely disable interaction and selection if disabled (AI turn / animation / active promotion)
        if self.disable_interaction or (self.chess_board_obj is not None and self.chess_board_obj.is_game_over()):
            return True # Consume touch event to lock the board
            
        # Identify which square widget was clicked
        for square in self.square_list:
            if square.collide_point(*touch.pos):
                self.handle_square_click(square)
                return True # Consume touch event
                
        return super().on_touch_down(touch)

    def _resize_board(self, instance, value):
        """Maintains the chessboard's square shape, aspect ratio, and centering on resize."""
        grid_size = min(self.width, self.height)
        self.board_grid.size = (grid_size, grid_size)
        
        # Centering the board grid inside the FloatLayout container
        self.board_grid.pos = (
            self.x + (self.width - grid_size) / 2,
            self.y + (self.height - grid_size) / 2
        )
