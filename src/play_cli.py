import sys
from pathlib import Path
import argparse
import chess

# Resolve the repository root (one level up from src/)
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.inference import ChessInference, MovePrediction

def print_game_state(board: chess.Board):
    """Prints the ASCII representation of the board along with metadata."""
    print("\n" + "=" * 40)
    print("BOARD STATUS:")
    print("=" * 40)
    print(board)
    print("=" * 40)
    print(f"FEN: {board.fen()}")
    print(f"Side to move: {'White' if board.turn == chess.WHITE else 'Black'}")
    print(f"Move number: {board.fullmove_number}")
    
    # Game status checks
    status = []
    if board.is_check():
        status.append("CHECK!")
    if board.is_game_over():
        status.append("GAME OVER")
    else:
        status.append("Active")
        
    print(f"Status: {', '.join(status)}")
    print("=" * 40 + "\n")

def check_game_over(board: chess.Board) -> bool:
    """Checks if the game has ended and prints the result."""
    if board.is_game_over():
        print("\n" + "#" * 40)
        print("GAME OVER")
        print("#" * 40)
        if board.is_checkmate():
            winner = "Black" if board.turn == chess.WHITE else "White"
            print(f"Result: Checkmate! {winner} wins.")
        elif board.is_stalemate():
            print("Result: Draw by Stalemate.")
        elif board.is_insufficient_material():
            print("Result: Draw due to insufficient material.")
        elif board.is_fifty_moves():
            print("Result: Draw by 50-move rule.")
        elif board.is_threefold_repetition():
            print("Result: Draw by threefold repetition.")
        else:
            print("Result: Draw by agreement or other rule.")
        print("#" * 40)
        return True
    return False

def print_move_history(history: list[str]):
    """Prints the game move history formatted in standard UCI notation ranks."""
    print("\n" + "=" * 40)
    print("MOVE HISTORY")
    print("=" * 40)
    for i, uci in enumerate(history):
        move_num = (i // 2) + 1
        if i % 2 == 0:
            print(f"{move_num}. {uci}")
        else:
            print(f"{move_num}... {uci}")
    print("=" * 40 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Human vs AI Chess Command-Line Interface")
    parser.add_argument("--color", choices=["white", "black"], help="Bypasses prompt and chooses human color")
    parser.add_argument("--moves", help="Comma-separated list of human moves for non-interactive automation")
    args = parser.parse_args()
    
    # Initialize the board and the AI inference engine
    board = chess.Board()
    try:
        ai = ChessInference()
    except Exception as e:
        print(f"Error: Failed to initialize AI inference engine: {e}")
        sys.exit(1)
        
    # Choose color
    human_color = None
    if args.color:
        if args.color == "white":
            human_color = chess.WHITE
        else:
            human_color = chess.BLACK
    else:
        while True:
            choice = input("Play as White (W) or Black (B)? ").strip().lower()
            if choice in ('w', 'white'):
                human_color = chess.WHITE
                break
            elif choice in ('b', 'black'):
                human_color = chess.BLACK
                break
            else:
                print("Invalid choice. Please enter 'W' or 'B'.")
                
    print(f"You are playing as: {'White' if human_color == chess.WHITE else 'Black'}")
    print("Enter 'quit' or 'exit' at any time to quit the game.")
    
    # Parse automated moves if provided
    auto_moves = []
    if args.moves:
        auto_moves = [m.strip() for m in args.moves.split(",") if m.strip()]
        
    history = []
    auto_idx = 0
    
    print_game_state(board)
    
    while not board.is_game_over():
        if board.turn == human_color:
            # Human's Turn
            print("--- Human Turn ---")
            move = None
            while True:
                if auto_idx < len(auto_moves):
                    move_input = auto_moves[auto_idx]
                    auto_idx += 1
                    print(f"Enter your move (UCI) [Auto]: {move_input}")
                else:
                    try:
                        move_input = input("Enter your move (UCI): ").strip()
                    except (EOFError, KeyboardInterrupt):
                        print("\nGame interrupted. Exiting.")
                        sys.exit(0)
                        
                if move_input.lower() in ('exit', 'quit'):
                    print("Game exited by user.")
                    print_move_history(history)
                    sys.exit(0)
                    
                try:
                    move = chess.Move.from_uci(move_input)
                except ValueError:
                    print(f"Invalid UCI syntax: '{move_input}'. Format example: 'e2e4', 'g1f3', 'e7e8q'.")
                    continue
                    
                if move in board.legal_moves:
                    break
                else:
                    print(f"Illegal move: '{move_input}'. Move is not legal in the current position.")
                    
            board.push(move)
            history.append(move.uci())
            print(f"Human played: {move.uci()}")
        else:
            # AI's Turn
            print("--- AI Turn ---")
            print("AI is thinking...")
            prediction = ai.predict_best_move(board.fen())
            
            if prediction.move is None or not prediction.is_legal:
                print("AI could not find a legal move or game is over.")
                break
                
            print(f"AI chooses: {prediction.uci}")
            board.push(prediction.move)
            history.append(prediction.uci)
            
        print_game_state(board)
        
    # Game ended
    check_game_over(board)
    print_move_history(history)

if __name__ == "__main__":
    main()
