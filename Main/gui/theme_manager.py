import sys
from pathlib import Path

class ThemeManager:
    """Centralized manager for application board themes and piece set path resolutions."""

    BOARD_THEMES = {
        "Classic": {
            "light": [240/255, 217/255, 181/255, 1.0],      # #F0D9B5
            "dark": [181/255, 136/255, 99/255, 1.0],         # #B58863
            "highlight": [186/255, 202/255, 43/255, 1.0],    # Soft selection green
            "legal_highlight": [72/255, 120/255, 209/255, 0.5] # Semi-transparent blue
        },
        "Green": {
            "light": [238/255, 238/255, 238/255, 1.0],      # #EEEEEE (Soft gray-white)
            "dark": [118/255, 150/255, 86/255, 1.0],         # #769656 (Chess.com Green)
            "highlight": [186/255, 202/255, 43/255, 0.8],    # Translucent green
            "legal_highlight": [118/255, 150/255, 86/255, 0.4] # Greenish highlights
        },
        "Blue": {
            "light": [233/255, 237/255, 240/255, 1.0],      # #E9EDF0 (Soft blue-white)
            "dark": [75/255, 115/255, 153/255, 1.0],         # #4B7399 (Chess.com Blue)
            "highlight": [228/255, 230/255, 134/255, 0.8],    # Soft yellow highlight
            "legal_highlight": [75/255, 115/255, 153/255, 0.4] # Blueish highlights
        },
        "Brown": {
            "light": [240/255, 220/255, 190/255, 1.0],      # Soft light wood
            "dark": [135/255, 95/255, 60/255, 1.0],         # Deep brown wood
            "highlight": [210/255, 180/255, 100/255, 0.8],   # Golden selection
            "legal_highlight": [135/255, 95/255, 60/255, 0.4] # Soft brown overlays
        },
        "Slate": {
            "light": [220/255, 224/255, 228/255, 1.0],      # Light slate
            "dark": [112/255, 128/255, 144/255, 1.0],        # Dark gray slate
            "highlight": [176/255, 196/255, 222/255, 0.8],   # Light blue slate
            "legal_highlight": [112/255, 128/255, 144/255, 0.4] # Semi-transparent slate
        }
    }

    PIECE_SETS = ["Unicode", "default", "alpha", "merida"]

    @classmethod
    def get_theme_colors(cls, theme_name: str) -> dict:
        """Validates the theme name and returns the theme configuration colors."""
        if theme_name not in cls.BOARD_THEMES:
            print(f"Warning: Invalid theme name '{theme_name}'. Reverting to Classic.")
            theme_name = "Classic"
        return cls.BOARD_THEMES[theme_name]

    @classmethod
    def get_piece_set_path(cls, piece_set_name: str, color: str, piece_type: str) -> str:
        """Returns the path to the piece image if it exists, otherwise None (causes Unicode fallback)."""
        if piece_set_name == "Unicode" or piece_set_name not in cls.PIECE_SETS:
            return None
            
        assets_dir = Path(__file__).resolve().parent / "assets" / "pieces" / piece_set_name
        image_filename = f"{color}_{piece_type}.png"
        image_path = assets_dir / image_filename
        
        if image_path.exists():
            return str(image_path)
        return None

    @classmethod
    def get_available_themes(cls) -> list:
        """Returns a list of all registered board theme names."""
        return list(cls.BOARD_THEMES.keys())

    @classmethod
    def get_available_piece_sets(cls) -> list:
        """Returns a list of all registered piece sets."""
        return cls.PIECE_SETS
