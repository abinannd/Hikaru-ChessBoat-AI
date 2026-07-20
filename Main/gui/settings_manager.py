import json
from pathlib import Path

class SettingsManager:
    """Manages persistent application settings inside a JSON configuration file."""

    DEFAULT_SETTINGS = {
        "app_theme": "Dark",
        "board_theme": "Classic",
        "piece_display": "Unicode",
        "animation_enabled": True,
        "animation_speed": "Normal",
        "ai_enabled": True,
        "ai_thinking_delay": 250,
        "auto_scroll_history": True
    }

    VALID_VALUES = {
        "app_theme": ["Light", "Dark"],
        "board_theme": ["Classic", "Green", "Blue", "Brown", "Slate"],
        "piece_display": ["Unicode", "default", "alpha", "merida"],
        "animation_enabled": [True, False],
        "animation_speed": ["Slow", "Normal", "Fast"],
        "ai_enabled": [True, False],
        "ai_thinking_delay": [0, 250, 500, 1000],
        "auto_scroll_history": [True, False]
    }

    def __init__(self, filename="settings.json"):
        # Resolve config storage filepath locally inside gui folder
        self.filepath = Path(__file__).resolve().parent / filename
        self.settings = {}
        self.load_settings()

    def load_settings(self):
        """Loads settings from JSON file, validates them, and falls back to defaults if invalid."""
        if not self.filepath.exists():
            self.settings = self.DEFAULT_SETTINGS.copy()
            self.save_settings()
            return
            
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
            
            self.settings = {}
            for key, default_val in self.DEFAULT_SETTINGS.items():
                val = data.get(key, default_val)
                if self._is_valid(key, val):
                    self.settings[key] = val
                else:
                    print(f"Warning: Invalid value for key '{key}': {val}. Reverting to default.")
                    self.settings[key] = default_val
        except Exception as e:
            print(f"Error loading settings file: {e}. Reverting to defaults.")
            self.settings = self.DEFAULT_SETTINGS.copy()
            
    def save_settings(self):
        """Persists settings immediately to JSON file."""
        try:
            with open(self.filepath, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key):
        """Retrieves the value of a setting, falling back to default if not found."""
        return self.settings.get(key, self.DEFAULT_SETTINGS.get(key))

    def set(self, key, value):
        """Sets a setting, validates it, and immediately saves to disk if valid."""
        if self._is_valid(key, value):
            self.settings[key] = value
            self.save_settings()
        else:
            raise ValueError(f"Invalid value '{value}' for setting key '{key}'")

    def _is_valid(self, key, value):
        """Checks if a value is valid for a setting key."""
        if key not in self.VALID_VALUES:
            return False
        # Match type exactly (since booleans are ints in Python, check type explicitly)
        expected_type = type(self.DEFAULT_SETTINGS[key])
        if type(value) is not expected_type:
            return False
        return value in self.VALID_VALUES[key]
