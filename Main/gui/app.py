import sys
from pathlib import Path

# Resolve directories to allow direct execution
GUI_ROOT = Path(__file__).resolve().parent
if str(GUI_ROOT) not in sys.path:
    sys.path.insert(0, str(GUI_ROOT))

from kivy.config import Config
# Set window size before loading Core Window to avoid glitches on some window systems
Config.set('graphics', 'width', '900')
Config.set('graphics', 'height', '650')
Config.set('graphics', 'resizable', '1')

from kivy.app import App
from main_window import MainWindow

class SupervisedChessAIApp(App):
    """Supervised Chess AI Kivy Application Entry Point."""
    
    def build(self):
        self.title = "Supervised Chess AI"
        
        # Load and assign custom application window/taskbar icon
        from utils.resource_path import resource_path
        self.icon = resource_path("Main/gui/assets/icons/chess_icon.png")
        
        return MainWindow()

if __name__ == "__main__":
    app = SupervisedChessAIApp()
    app.run()
