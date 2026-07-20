import sys
import os
from pathlib import Path

def resource_path(relative_path: str) -> str:
    """Resolves absolute path to resources in both development mode and PyInstaller bundles.
    
    If running as a PyInstaller executable, routes path to the temporary _MEIPASS folder.
    Otherwise, routes to the repository root directory.
    """
    try:
        # PyInstaller extracts bundled files to sys._MEIPASS at runtime
        base_path = sys._MEIPASS
    except Exception:
        # Resolve base path as the repository root directory (3 levels up from this file)
        base_path = str(Path(__file__).resolve().parents[3])
        
    return os.path.abspath(os.path.join(base_path, relative_path))
