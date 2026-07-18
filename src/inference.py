import sys
from pathlib import Path
import torch

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Main.chess_model import ChessMoveCNN

def load_chess_model(checkpoint_path: Path | str | None = None) -> ChessMoveCNN:
    """Reconstructs the ChessMoveCNN architecture, loads weights from best_model.pth,

    and switches it to evaluation mode.
    """
    if checkpoint_path is None:
        checkpoint_path = REPO_ROOT / "Main" / "models" / "best_model.pth"
    checkpoint_path = Path(checkpoint_path)

    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint file not found at: {checkpoint_path}")

    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location="cpu")

    # Reconstruct CNN architecture
    model = ChessMoveCNN()

    # Load weights correctly
    if "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        model.load_state_dict(checkpoint)

    # Switch model to evaluation mode
    model.eval()

    # Verify model has loaded successfully and is in eval mode
    assert not model.training, "Error: Model was not put into evaluation mode."

    return model

if __name__ == "__main__":
    try:
        model = load_chess_model()
        print("Model successfully loaded.")
    except Exception as e:
        print(f"Error loading model: {e}")
        sys.exit(1)
