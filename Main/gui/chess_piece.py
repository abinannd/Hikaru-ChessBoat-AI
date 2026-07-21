import sys
from pathlib import Path

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label

import os
from kivy.core.text import LabelBase

# Register Segoe UI Symbol system font for chess characters on Windows
HAS_SEGOE_UI_SYMBOL = False
if sys.platform == "win32":
    font_path = r"C:\Windows\Fonts\seguisym.ttf"
    if os.path.exists(font_path):
        try:
            LabelBase.register(name="Segoe UI Symbol", fn_regular=font_path)
            HAS_SEGOE_UI_SYMBOL = True
        except Exception as e:
            print(f"Warning: Failed to register Segoe UI Symbol: {e}")

# Unicode fallbacks for chess pieces
UNICODE_PIECES = {
    'w': {
        'king': '♔',
        'queen': '♕',
        'rook': '♖',
        'bishop': '♗',
        'knight': '♘',
        'pawn': '♙'
    },
    'b': {
        'king': '♚',
        'queen': '♛',
        'rook': '♜',
        'bishop': '♝',
        'knight': '♞',
        'pawn': '♟'
    }
}

class ChessPiece(BoxLayout):
    """Widget representing a chess piece (Presentation layer only)."""

    def __init__(self, piece_type: str, color: str, use_images: bool = True, piece_display_setting: str = "Unicode", **kwargs):
        super().__init__(**kwargs)
        self.piece_type = piece_type  # 'pawn', 'knight', 'bishop', 'rook', 'queen', 'king'
        self.color = color            # 'w' (White) or 'b' (Black)
        self.orientation = 'vertical'
        self.padding = 2

        # Use ThemeManager to resolve custom asset pathways
        from theme_manager import ThemeManager
        image_path = ThemeManager.get_piece_set_path(piece_display_setting, self.color, self.piece_type)

        if use_images and image_path is not None:
            # Load and display standard image asset from verified directory
            self.piece_img = Image(source=image_path, allow_stretch=True, keep_ratio=True)
            self.add_widget(self.piece_img)
        else:
            # Fallback to high-quality unicode character rendering
            symbol = UNICODE_PIECES[self.color][self.piece_type]
            label_color = [1.0, 0.95, 0.9, 1.0] if self.color == 'w' else [0.15, 0.15, 0.15, 1.0]
            font_name = "Segoe UI Symbol" if HAS_SEGOE_UI_SYMBOL else None
            self.piece_lbl = Label(
                text=symbol,
                font_name=font_name,
                color=label_color,
                bold=True,
                halign='center',
                valign='middle'
            )
            # Bind layout resizing to scale the font size and text box bounds dynamically
            self.bind(size=self._scale_piece)
            self.add_widget(self.piece_lbl)

    def _scale_piece(self, instance, value):
        """Maintains clean font scale and text alignment bounds inside the square."""
        if hasattr(self, 'piece_lbl'):
            self.piece_lbl.font_size = self.height * 0.75
            self.piece_lbl.text_size = self.size
