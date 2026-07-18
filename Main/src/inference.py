import sys
from pathlib import Path
import torch
import chess

# Resolve the repository root (two levels up from Main/src/)
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Main.chess_model import ChessMoveCNN

class ChessInference:
    """Class to handle model loading, board representation, encoding, and inference for the chess model."""
    
    def __init__(self, checkpoint_path: str | Path | None = None):
        # Detect CUDA automatically
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        if checkpoint_path is None:
            self.checkpoint_path = REPO_ROOT / "Main" / "models" / "best_model.pth"
        else:
            self.checkpoint_path = Path(checkpoint_path)
            
        self.board = None
            
        # Reconstruct and load model
        self.model = self._load_model()
        
    def _load_model(self) -> ChessMoveCNN:
        if not self.checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint file not found at: {self.checkpoint_path}")
            
        try:
            checkpoint = torch.load(self.checkpoint_path, map_location=self.device, weights_only=False)
        except Exception as e:
            raise RuntimeError(f"Failed to load checkpoint file: {e}")
            
        model = ChessMoveCNN()
        
        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            model.load_state_dict(checkpoint["model_state_dict"])
            epoch = checkpoint.get("epoch", "N/A")
            val_loss = checkpoint.get("val_loss", "N/A")
            val_acc = checkpoint.get("val_acc", "N/A")
        else:
            model.load_state_dict(checkpoint)
            epoch = "N/A"
            val_loss = "N/A"
            val_acc = "N/A"
            
        model.to(self.device)
        model.eval()
        
        assert not model.training, "Error: Model was not put into evaluation mode."
        
        print(f"Device: {self.device}")
        print(f"Stored epoch: {epoch}")
        if isinstance(val_loss, (int, float)):
            print(f"Validation loss: {val_loss:.4f}")
        else:
            print(f"Validation loss: {val_loss}")
            
        if isinstance(val_acc, (int, float)):
            print(f"Validation accuracy: {val_acc * 100:.2f}%")
        else:
            print(f"Validation accuracy: {val_acc}")
            
        print("Model successfully loaded.")
        return model

    def load_board(self, fen: str) -> None:
        """Accepts a FEN string, validates it using python-chess, and stores the board.
        
        Raises ValueError if the FEN is invalid or represents an illegal board state.
        """
        try:
            board = chess.Board(fen)
            # Semantic check for legal chess positions
            if not board.is_valid():
                errors = []
                status = board.status()
                if status & chess.STATUS_NO_WHITE_KING:
                    errors.append("No White King")
                if status & chess.STATUS_NO_BLACK_KING:
                    errors.append("No Black King")
                if status & chess.STATUS_TOO_MANY_KINGS:
                    errors.append("Too Many Kings")
                if status & chess.STATUS_TOO_MANY_CHECKERS:
                    errors.append("Too Many Checkers")
                if status & chess.STATUS_PAWNS_ON_BACKRANK:
                    errors.append("Pawns on backrank")
                error_str = ", ".join(errors) if errors else "Illegal chess position"
                raise ValueError(f"FEN represents an illegal chess position: {error_str}")
                
            self.board = board
        except ValueError as e:
            raise ValueError(f"Invalid FEN string: {e}")

    def display_board(self) -> None:
        """Prints the ASCII representation of the board and other state details."""
        if self.board is None:
            print("No board loaded.")
            return
            
        print("Board ASCII Representation:")
        print(self.board)
        print("-" * 30)
        print(f"Side to move: {'White' if self.board.turn == chess.WHITE else 'Black'}")
        
        # Castling rights formatting
        rights_str = []
        if self.board.has_kingside_castling_rights(chess.WHITE):
            rights_str.append("K")
        if self.board.has_queenside_castling_rights(chess.WHITE):
            rights_str.append("Q")
        if self.board.has_kingside_castling_rights(chess.BLACK):
            rights_str.append("k")
        if self.board.has_queenside_castling_rights(chess.BLACK):
            rights_str.append("q")
        print(f"Castling rights: {''.join(rights_str) if rights_str else '-'}")
        
        # En passant
        ep_square = self.board.ep_square
        ep_str = chess.square_name(ep_square) if ep_square is not None else "-"
        print(f"En passant square: {ep_str}")
        
        # Clocks and move counts
        print(f"Halfmove clock: {self.board.halfmove_clock}")
        print(f"Fullmove number: {self.board.fullmove_number}")
        print("=" * 40)

    def encode_current_board(self) -> torch.Tensor:
        """Encodes the internally stored board state using the existing board encoder,
        converts it to a PyTorch float32 tensor on the correct device, and adds a batch dimension.
        """
        if self.board is None:
            raise ValueError("No board loaded to encode.")
            
        # Reuse the existing board encoder from board_encoder.py
        # Lazy import to ensure clean paths
        from Main.board_encoder import encode_board
        import numpy as np
        
        # 1. Encode the board using the existing encoder logic
        encoded_np = encode_board(self.board)
        
        # 2. Convert the encoded board into a PyTorch tensor (dtype float32)
        board_tensor = torch.from_numpy(encoded_np.astype(np.float32, copy=False))
        
        # 3. Add batch dimension -> shape (1, 18, 8, 8)
        board_tensor = board_tensor.unsqueeze(0)
        
        # 4. Move the tensor to the model's device
        board_tensor = board_tensor.to(self.device)
        
        # 5. Print verification information
        print(f"Original encoded shape: {encoded_np.shape}")
        print(f"Tensor shape: {tuple(board_tensor.shape)}")
        print(f"Tensor dtype: {board_tensor.dtype}")
        print(f"Device: {board_tensor.device}")
        print(f"Minimum tensor value: {float(board_tensor.min())}")
        print(f"Maximum tensor value: {float(board_tensor.max())}")
        
        return board_tensor

if __name__ == "__main__":
    try:
        inference = ChessInference()
        print("\n" + "="*40 + "\nRUNNING BOARD ENCODING VERIFICATION SUITE\n" + "="*40)
        
        # Test positions
        test_positions = {
            "Initial Position": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "Midgame": "r1bq1rk1/pp2bppp/2np1n2/2p1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 8",
            "Endgame": "8/5pk1/8/8/8/8/5PK1/8 w - - 0 1",
            "Promotion Position": "4k3/P7/8/8/8/8/7p/4K3 w - - 0 1",
            "Checkmate Position": "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"
        }
        
        # Run validation and encoding tests
        for name, fen in test_positions.items():
            print(f"Testing {name}:")
            print(f"FEN: {fen}")
            try:
                # Step 2 Load & Display
                inference.load_board(fen)
                print("[OK] FEN parsed successfully")
                print("[OK] Board created")
                
                # Step 3 Encode & Verify
                tensor = inference.encode_current_board()
                
                # Assertions to programmatic verify correctness
                assert tensor.shape == (1, 18, 8, 8), f"Incorrect shape: {tensor.shape}"
                assert tensor.dtype == torch.float32, f"Incorrect dtype: {tensor.dtype}"
                assert tensor.device.type == inference.device.type, f"Incorrect device type: {tensor.device} vs {inference.device}"
                
                print("[OK] Encoding successful")
                print("[OK] Tensor shape is (1, 18, 8, 8)")
                print("[OK] Correct tensor dtype (float32)")
                print("[OK] Tensor transferred to correct device")
                print("-" * 40)
            except Exception as e:
                print(f"[FAILED] Failed testing {name}: {e}\n")
                sys.exit(1)
                
        print("Verification Suite completed successfully.")
        
    except Exception as e:
        print(f"Verification failed: {e}")
        sys.exit(1)
