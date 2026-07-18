import sys
from pathlib import Path
from dataclasses import dataclass
import torch
import chess

# Resolve the repository root (one level up from src/)
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.chess_model import ChessMoveCNN

@dataclass
class MovePrediction:
    """A structured representation of a move prediction output from the model."""
    move: chess.Move | None
    uci: str | None
    class_id: int | None
    logit: float | None
    is_legal: bool

class ChessInference:
    """Class to handle model loading, board representation, encoding, and inference for the chess model."""
    
    def __init__(self, checkpoint_path: str | Path | None = None):
        # Detect CUDA automatically
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        if checkpoint_path is None:
            self.checkpoint_path = REPO_ROOT / "models" / "best_model.pth"
        else:
            self.checkpoint_path = Path(checkpoint_path)
            
        self.board = None
        self.current_tensor = None
        self.logits = None
            
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
            self.current_tensor = None
            self.logits = None
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
            
        # Reuse the existing board encoder from src.board_encoder.py
        # Lazy import to ensure clean paths
        from src.board_encoder import encode_board
        import numpy as np
        
        # 1. Encode the board using the existing encoder logic
        encoded_np = encode_board(self.board)
        
        # 2. Convert the encoded board into a PyTorch tensor (dtype float32)
        board_tensor = torch.from_numpy(encoded_np.astype(np.float32, copy=False))
        
        # 3. Add batch dimension -> shape (1, 18, 8, 8)
        board_tensor = board_tensor.unsqueeze(0)
        
        # 4. Move the tensor to the model's device
        board_tensor = board_tensor.to(self.device)
        self.current_tensor = board_tensor
        
        # 5. Print verification information
        print(f"Original encoded shape: {encoded_np.shape}")
        print(f"Tensor shape: {tuple(board_tensor.shape)}")
        print(f"Tensor dtype: {board_tensor.dtype}")
        print(f"Device: {board_tensor.device}")
        print(f"Minimum tensor value: {float(board_tensor.min())}")
        print(f"Maximum tensor value: {float(board_tensor.max())}")
        
        return board_tensor

    def predict_logits(self) -> torch.Tensor:
        """Runs the encoded board tensor through the trained CNN inside a torch.no_grad() block.
        
        Stores the raw output logits internally in self.logits.
        Returns the output logits of shape (1, 4272).
        """
        if self.board is None:
            raise ValueError("No board loaded. Call load_board() first.")
        if self.current_tensor is None:
            raise ValueError("Board has not been encoded yet. Call encode_current_board() first.")
            
        with torch.no_grad():
            self.logits = self.model(self.current_tensor)
            
        # Print verification information
        print(f"Input tensor shape: {tuple(self.current_tensor.shape)}")
        print(f"Output tensor shape: {tuple(self.logits.shape)}")
        print(f"Output dtype: {self.logits.dtype}")
        print(f"Device: {self.logits.device}")
        print(f"Number of output classes: {self.logits.shape[1]}")
        print(f"Minimum logit value: {float(self.logits.min()):.4f}")
        print(f"Maximum logit value: {float(self.logits.max()):.4f}")
        
        # Compute and print top-10 predicted class indices and raw logit values
        top_logits, top_indices = torch.topk(self.logits, k=10, dim=1)
        print("Top-10 predicted class indices and raw logit values:")
        for rank, (idx, logit) in enumerate(zip(top_indices[0].tolist(), top_logits[0].tolist()), 1):
            print(f"  Rank {rank:2d}: Class {idx:4d} | Logit: {logit:.6f}")
            
        return self.logits

    def decode_predictions(self, top_k: int = 10) -> list[MovePrediction]:
        """Obtains the top-k predicted class indices from the logits and decodes them into MovePrediction objects.
        
        Reuses the existing move_encoder.decode_move but bypasses position legality checks.
        """
        if self.logits is None:
            raise ValueError("No logits found. Run predict_logits() first.")
            
        from src.move_encoder import decode_move
        
        # Bypasses the legality checks inside decode_move by providing a duck-typed board
        class MockBoard:
            @property
            def legal_moves(self):
                class AllLegal:
                    def __contains__(self, item):
                        return True
                return AllLegal()
                
        mock_board = MockBoard()
        
        top_logits, top_indices = torch.topk(self.logits, k=top_k, dim=1)
        
        decoded_results = []
        for rank, (idx, logit) in enumerate(zip(top_indices[0].tolist(), top_logits[0].tolist()), 1):
            move = decode_move(idx, board=mock_board)
            move_str = move.uci()
            is_legal = (self.board is not None and move in self.board.legal_moves)
            
            prediction = MovePrediction(
                move=move,
                uci=move_str,
                class_id=idx,
                logit=logit,
                is_legal=is_legal
            )
            decoded_results.append(prediction)
            
            # Print in the format required by phase-4.txt
            print(f"Rank {rank}")
            print(f"Class ID: {idx}")
            print(f"Logit: {logit:.4f}")
            print(f"Move: {move_str}")
            print()
            
        return decoded_results

    def get_best_legal_move(self) -> MovePrediction:
        """Scores all legal moves in the current position based on the pre-computed logits,
        and selects the move with the highest logit score.
        
        Returns:
            A MovePrediction object representing the best legal move, or a MovePrediction
            with None fields and is_legal=False if no legal moves exist.
        """
        if self.board is None:
            raise ValueError("No board loaded. Call load_board() first.")
        if self.logits is None:
            raise ValueError("No logits found. Run predict_logits() first.")
            
        from src.move_encoder import encode_move
        
        # 1. Legal Move Generation
        legal_moves = list(self.board.legal_moves)
        print(f"Board FEN: {self.board.fen()}")
        print(f"Number of legal moves: {len(legal_moves)}")
        
        if not legal_moves:
            if self.board.is_checkmate():
                print("Game Over: Checkmate")
            else:
                print("Game Over: Stalemate/Draw")
            return MovePrediction(move=None, uci=None, class_id=None, logit=None, is_legal=False)
            
        # 2. Move Scoring
        scored_moves = []
        for move in legal_moves:
            try:
                class_idx = encode_move(move)
                # Read the corresponding logit directly from the model output
                logit_score = float(self.logits[0, class_idx].item())
                scored_moves.append((move, class_idx, logit_score))
            except Exception as e:
                # Fallback / handling just in case of encoding issues
                print(f"Warning: Failed to encode legal move {move.uci()}: {e}")
                
        if not scored_moves:
            raise RuntimeError("None of the legal moves could be encoded.")
            
        # Sort moves by logit score descending
        scored_moves.sort(key=lambda x: x[2], reverse=True)
        
        # 3. Move Selection
        best_move, best_class_id, best_logit_score = scored_moves[0]
        best_move_uci = best_move.uci()
        
        # Print Verification Output
        print(f"Best legal move: {best_move_uci}")
        print(f"Class ID: {best_class_id}")
        print(f"Logit score: {best_logit_score:.4f}")
        
        # Print top 10 legal moves ranked by score
        print("Top 10 legal moves ranked by score:")
        for rank, (move, class_idx, score) in enumerate(scored_moves[:10], 1):
            print(f"  Rank {rank:2d}: Move {move.uci()} | Class ID {class_idx:4d} | Logit {score:.4f}")
            
        return MovePrediction(
            move=best_move,
            uci=best_move_uci,
            class_id=best_class_id,
            logit=best_logit_score,
            is_legal=True
        )

    def predict_best_move(self, fen: str) -> MovePrediction:
        """Executes the complete move prediction pipeline for a given FEN string:
        1. Loads the FEN.
        2. Encodes the board.
        3. Runs neural network inference.
        4. Generates logits.
        5. Generates all legal moves.
        6. Scores every legal move.
        7. Selects the highest-scoring legal move.
        8. Returns a MovePrediction object.
        
        Measures performance of each step.
        """
        import time
        
        t_start = time.perf_counter()
        
        # 1. Load FEN
        t0 = time.perf_counter()
        self.load_board(fen)
        t_load = (time.perf_counter() - t0) * 1000  # milliseconds
        
        # 2. Encode board
        t0 = time.perf_counter()
        self.encode_current_board()
        t_encode = (time.perf_counter() - t0) * 1000  # milliseconds
        
        # 3. NN inference (forward pass & logits generation)
        t0 = time.perf_counter()
        self.predict_logits()
        t_inference = (time.perf_counter() - t0) * 1000  # milliseconds
        
        # 4. Legal Move scoring & selection
        t0 = time.perf_counter()
        prediction = self.get_best_legal_move()
        t_eval = (time.perf_counter() - t0) * 1000  # milliseconds
        
        t_total = (time.perf_counter() - t_start) * 1000  # milliseconds
        
        # Console Output
        print("=====================================")
        print("AI Prediction")
        print("=====================================")
        print(f"FEN: {fen}")
        print(f"Side to move: {'White' if self.board.turn == chess.WHITE else 'Black'}")
        print(f"Number of legal moves: {len(list(self.board.legal_moves)) if self.board else 0}")
        print(f"Chosen move: {prediction.uci if prediction.uci else 'None'}")
        print(f"Class ID: {prediction.class_id if prediction.class_id is not None else 'None'}")
        print(f"Logit: {prediction.logit if prediction.logit is not None else 'None'}")
        print(f"Legal: {prediction.is_legal}")
        print(f"Inference device: {self.device}")
        print(f"Inference time (milliseconds): {t_inference:.2f} ms")
        print("-" * 37)
        print("Performance Metrics:")
        print(f"  Board loading time:         {t_load:.2f} ms")
        print(f"  Encoding time:              {t_encode:.2f} ms")
        print(f"  Inference time:             {t_inference:.2f} ms")
        print(f"  Legal move evaluation time: {t_eval:.2f} ms")
        print(f"  Total prediction time:      {t_total:.2f} ms")
        print("=====================================")
        
        return prediction

if __name__ == "__main__":
    try:
        inference = ChessInference()
        print("\n" + "="*40 + "\nRUNNING BOARD ENCODING, INFERENCE & DECODING VERIFICATION SUITE\n" + "="*40)
        
        # Test positions
        test_positions = {
            "Initial Position": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "Midgame": "r1bq1rk1/pp2bppp/2np1n2/2p1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 8",
            "Endgame": "8/5pk1/8/8/8/8/5PK1/8 w - - 0 1",
            "Promotion Position": "4k3/P7/8/8/8/8/7p/4K3 w - - 0 1",
            "Checkmate Position": "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"
        }
        
        # Run validation, encoding, inference, decoding, filtering, and unified pipeline tests
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
                
                # Assertions to programmatically verify correctness
                assert tensor.shape == (1, 18, 8, 8), f"Incorrect shape: {tensor.shape}"
                assert tensor.dtype == torch.float32, f"Incorrect dtype: {tensor.dtype}"
                assert tensor.device.type == inference.device.type, f"Incorrect device type: {tensor.device} vs {inference.device}"
                
                print("[OK] Encoding successful")
                print("[OK] Tensor shape is (1, 18, 8, 8)")
                print("[OK] Correct tensor dtype (float32)")
                print("[OK] Tensor transferred to correct device")
                
                # Step 4 Inference & Verify
                logits = inference.predict_logits()
                assert logits.shape == (1, 4272), f"Incorrect logits shape: {logits.shape}"
                assert logits.dtype == torch.float32, f"Incorrect logits dtype: {logits.dtype}"
                assert logits.device.type == inference.device.type, f"Incorrect logits device type: {logits.device} vs {inference.device}"
                print("[OK] Inference successful, logits shape is (1, 4272)")
                
                # Step 5 Decoding & Verify
                print("Decoded top 10 predictions:")
                decoded = inference.decode_predictions(10)
                assert len(decoded) == 10, f"Expected 10 decoded predictions, got {len(decoded)}"
                for pred in decoded:
                    assert isinstance(pred, MovePrediction)
                    assert isinstance(pred.class_id, int)
                    assert isinstance(pred.logit, float)
                    move_str = pred.uci
                    # Verify basic UCI move format
                    assert len(move_str) in (4, 5), f"Invalid UCI length: {move_str}"
                    assert move_str[0] in "abcdefgh", f"Invalid start file: {move_str}"
                    assert move_str[1] in "12345678", f"Invalid start rank: {move_str}"
                    assert move_str[2] in "abcdefgh", f"Invalid end file: {move_str}"
                    assert move_str[3] in "12345678", f"Invalid end rank: {move_str}"
                    if len(move_str) == 5:
                        assert move_str[4] in "qrbn", f"Invalid promotion piece: {move_str}"
                print("[OK] Decoding successful and format verified")
                
                # Step 6 Legal Move Filtering & Verify
                best_pred = inference.get_best_legal_move()
                assert isinstance(best_pred, MovePrediction)
                if name == "Checkmate Position":
                    assert best_pred.move is None, f"Expected None for checkmate, got {best_pred.move}"
                    assert best_pred.uci is None
                    assert best_pred.class_id is None
                    assert best_pred.logit is None
                    assert best_pred.is_legal is False
                    print("[OK] Checkmate position handled correctly (returned None prediction)")
                else:
                    assert best_pred.move is not None, "Expected a legal move, got None"
                    assert best_pred.is_legal is True
                    assert best_pred.move in inference.board.legal_moves, f"Move {best_pred.uci} is not legal on this board!"
                    assert best_pred.uci == best_pred.move.uci()
                    assert isinstance(best_pred.class_id, int)
                    assert isinstance(best_pred.logit, float)
                    print(f"[OK] Best legal move selected: {best_pred.uci}")
                print("[OK] Legal move filtering successful")
                
                # Step 7 Pipeline Verification
                print("Running Step 7 unified pipeline...")
                pipeline_pred = inference.predict_best_move(fen)
                assert isinstance(pipeline_pred, MovePrediction)
                if name == "Checkmate Position":
                    assert pipeline_pred.move is None
                    assert pipeline_pred.is_legal is False
                else:
                    assert pipeline_pred.move is not None
                    assert pipeline_pred.is_legal is True
                    assert pipeline_pred.move == best_pred.move
                print("[OK] Step 7 pipeline run successful and verified")
                print("-" * 40)
            except Exception as e:
                print(f"[FAILED] Failed testing {name}: {e}\n")
                sys.exit(1)
                
        # Run invalid FEN test explicitly to satisfy requirements
        print("Testing Invalid FEN handling:")
        try:
            inference.predict_best_move("invalid fen string here")
            print("[FAILED] Expected ValueError for invalid FEN, but none was raised.")
            sys.exit(1)
        except ValueError as e:
            print(f"[OK] Invalid FEN correctly raised exception: {e}")
            
        print("Verification Suite completed successfully.")
        
    except Exception as e:
        print(f"Verification failed: {e}")
        sys.exit(1)
