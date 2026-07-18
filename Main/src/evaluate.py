import sys
from pathlib import Path
import argparse
import time
import contextlib
import io
import torch
import chess
import chess.pgn

# Resolve the repository root (two levels up from Main/src/)
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Main.src.inference import ChessInference, MovePrediction

def main():
    parser = argparse.ArgumentParser(description="AI Move Prediction Evaluation Utility")
    parser.add_argument("--pgn", type=str, default=str(REPO_ROOT / "Main" / "data" / "splits" / "test.pgn"),
                        help="Path to evaluation PGN file")
    parser.add_argument("--subset", type=int, default=None,
                        help="Number of games to evaluate (default: all)")
    parser.add_argument("--output-dir", type=str, default=str(REPO_ROOT),
                        help="Output directory for report files")
    args = parser.parse_args()

    pgn_path = Path(args.pgn)
    output_dir = Path(args.output_dir)

    print(f"PGN Path: {pgn_path.resolve()}")
    if not pgn_path.exists():
        print(f"Error: PGN file not found: {pgn_path}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize inference engine
    print("Loading AI inference engine...")
    try:
        inference = ChessInference()
    except Exception as e:
        print(f"Error: Failed to initialize ChessInference: {e}")
        sys.exit(1)

    # Statistics dict
    stats = {
        "total_positions": 0,
        "top1_correct": 0,
        "top3_correct": 0,
        "top5_correct": 0,
        "top10_correct": 0,
        "total_inference_time_ms": 0.0,
        "total_legal_moves_count": 0,
        "prediction_failures": 0,
        "invalid_positions_skipped": 0,
        "total_games_processed": 0,
        
        "phases": {
            "opening": {"count": 0, "top1": 0, "top3": 0, "top5": 0, "top10": 0},
            "middlegame": {"count": 0, "top1": 0, "top3": 0, "top5": 0, "top10": 0},
            "endgame": {"count": 0, "top1": 0, "top3": 0, "top5": 0, "top10": 0},
        },
        
        "outcomes": {
            "white_wins": {"count": 0, "top1": 0, "top3": 0, "top5": 0, "top10": 0},
            "black_wins": {"count": 0, "top1": 0, "top3": 0, "top5": 0, "top10": 0},
            "draws": {"count": 0, "top1": 0, "top3": 0, "top5": 0, "top10": 0},
        }
    }

    t_eval_start = time.perf_counter()

    print(f"Starting evaluation on PGN: {pgn_path.name}")
    if args.subset:
        print(f"Evaluating subset of first {args.subset} games.")
    else:
        print("Evaluating all games in PGN.")

    with pgn_path.open("r", encoding="utf-8") as handle:
        game_idx = 0
        while True:
            if args.subset and game_idx >= args.subset:
                break
                
            try:
                game = chess.pgn.read_game(handle)
            except Exception as e:
                print(f"Skipping malformed PGN game: {e}")
                stats["invalid_positions_skipped"] += 1
                continue
                
            if game is None:
                break
                
            game_idx += 1
            stats["total_games_processed"] += 1
            
            # Read game outcome
            result = game.headers.get("Result", "*")
            outcome_key = None
            if result == "1-0":
                outcome_key = "white_wins"
            elif result == "0-1":
                outcome_key = "black_wins"
            elif result == "1/2-1/2":
                outcome_key = "draws"

            board = game.board()
            
            # Replay game move by move
            for move in game.mainline_moves():
                fen = board.fen()
                
                try:
                    # 1. Load board FEN
                    inference.load_board(fen)
                    # 2. Encode board (suppress verbose logs)
                    with contextlib.redirect_stdout(io.StringIO()):
                        inference.encode_current_board()
                except Exception as e:
                    print(f"Skipping invalid position in FEN '{fen}': {e}")
                    stats["invalid_positions_skipped"] += 1
                    continue
                    
                # 3. Generate predictions (forward pass & timing, suppress verbose logs)
                t0 = time.perf_counter()
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        logits = inference.predict_logits()
                except Exception as e:
                    print(f"Prediction failed for FEN '{fen}': {e}")
                    stats["prediction_failures"] += 1
                    continue
                inf_time_ms = (time.perf_counter() - t0) * 1000
                
                # Fetch count of legal moves
                num_legal_moves = len(list(board.legal_moves))
                
                # Encode the actual move played
                try:
                    from Main.move_encoder import encode_move
                    actual_class_id = encode_move(move)
                except Exception as e:
                    stats["prediction_failures"] += 1
                    continue
                    
                # Sort logits to evaluate top-k
                top_logits, top_indices = torch.topk(logits, k=10, dim=1)
                top_indices = top_indices[0].tolist()
                
                is_top1 = (actual_class_id == top_indices[0])
                is_top3 = (actual_class_id in top_indices[:3])
                is_top5 = (actual_class_id in top_indices[:5])
                is_top10 = (actual_class_id in top_indices[:10])
                
                # Update general stats
                stats["total_positions"] += 1
                stats["total_inference_time_ms"] += inf_time_ms
                stats["total_legal_moves_count"] += num_legal_moves
                
                if is_top1: stats["top1_correct"] += 1
                if is_top3: stats["top3_correct"] += 1
                if is_top5: stats["top5_correct"] += 1
                if is_top10: stats["top10_correct"] += 1
                
                # Determine phase
                move_number = board.fullmove_number
                if move_number <= 10:
                    phase_key = "opening"
                elif move_number <= 40:
                    phase_key = "middlegame"
                else:
                    phase_key = "endgame"
                    
                stats["phases"][phase_key]["count"] += 1
                if is_top1: stats["phases"][phase_key]["top1"] += 1
                if is_top3: stats["phases"][phase_key]["top3"] += 1
                if is_top5: stats["phases"][phase_key]["top5"] += 1
                if is_top10: stats["phases"][phase_key]["top10"] += 1
                
                # Determine outcome stats
                if outcome_key:
                    stats["outcomes"][outcome_key]["count"] += 1
                    if is_top1: stats["outcomes"][outcome_key]["top1"] += 1
                    if is_top3: stats["outcomes"][outcome_key]["top3"] += 1
                    if is_top5: stats["outcomes"][outcome_key]["top5"] += 1
                    if is_top10: stats["outcomes"][outcome_key]["top10"] += 1
                    
                # Push move to proceed
                board.push(move)
                
            if game_idx % 10 == 0:
                print(f"Processed {game_idx} games... (Total positions: {stats['total_positions']})")

    t_eval_end = time.perf_counter()
    eval_duration_sec = t_eval_end - t_eval_start

    # Safety checks for division by zero
    total_pos = stats["total_positions"]
    if total_pos == 0:
        print("Error: No positions evaluated.")
        sys.exit(1)

    # Compute overall percentages
    top1_pct = (stats["top1_correct"] / total_pos) * 100
    top3_pct = (stats["top3_correct"] / total_pos) * 100
    top5_pct = (stats["top5_correct"] / total_pos) * 100
    top10_pct = (stats["top10_correct"] / total_pos) * 100
    avg_inf_time = stats["total_inference_time_ms"] / total_pos
    avg_legal_moves = stats["total_legal_moves_count"] / total_pos

    # Console Output formatting
    print("\n" + "=" * 50)
    print("EVALUATION COMPLETED SUCCESSFULLY")
    print("=" * 50)
    print(f"Total Games Processed:      {stats['total_games_processed']}")
    print(f"Total Positions Evaluated:  {total_pos}")
    print(f"Evaluation Duration:        {eval_duration_sec:.2f} seconds")
    print(f"Average Inference Time:     {avg_inf_time:.2f} ms")
    print(f"Average Legal Moves:        {avg_legal_moves:.1f}")
    print(f"Prediction Failures:        {stats['prediction_failures']}")
    print(f"Invalid Positions Skipped:  {stats['invalid_positions_skipped']}")
    print("-" * 50)
    print("PREDICTION ACCURACY:")
    print(f"  Top-1 Accuracy:  {top1_pct:.2f}%")
    print(f"  Top-3 Accuracy:  {top3_pct:.2f}%")
    print(f"  Top-5 Accuracy:  {top5_pct:.2f}%")
    print(f"  Top-10 Accuracy: {top10_pct:.2f}%")
    print("-" * 50)
    
    print("PERFORMANCE BY GAME PHASE:")
    print("Phase       | Positions | Top-1    | Top-3    | Top-5    | Top-10")
    print("------------|-----------|----------|----------|----------|----------")
    for phase in ("opening", "middlegame", "endgame"):
        p_data = stats["phases"][phase]
        p_count = p_data["count"]
        if p_count > 0:
            p_top1 = (p_data["top1"] / p_count) * 100
            p_top3 = (p_data["top3"] / p_count) * 100
            p_top5 = (p_data["top5"] / p_count) * 100
            p_top10 = (p_data["top10"] / p_count) * 100
            print(f"{phase.capitalize():11s} | {p_count:9d} | {p_top1:7.2f}% | {p_top3:7.2f}% | {p_top5:7.2f}% | {p_top10:7.2f}%")
        else:
            print(f"{phase.capitalize():11s} | {p_count:9d} | N/A      | N/A      | N/A      | N/A")
    print("-" * 50)

    print("PERFORMANCE BY GAME OUTCOME:")
    print("Outcome     | Positions | Top-1    | Top-3    | Top-5    | Top-10")
    print("------------|-----------|----------|----------|----------|----------")
    for outcome_name, outcome_label in (("white_wins", "White Wins"), ("black_wins", "Black Wins"), ("draws", "Draws")):
        o_data = stats["outcomes"][outcome_name]
        o_count = o_data["count"]
        if o_count > 0:
            o_top1 = (o_data["top1"] / o_count) * 100
            o_top3 = (o_data["top3"] / o_count) * 100
            o_top5 = (o_data["top5"] / o_count) * 100
            o_top10 = (o_data["top10"] / o_count) * 100
            print(f"{outcome_label:11s} | {o_count:9d} | {o_top1:7.2f}% | {o_top3:7.2f}% | {o_top5:7.2f}% | {o_top10:7.2f}%")
        else:
            print(f"{outcome_label:11s} | {o_count:9d} | N/A      | N/A      | N/A      | N/A")
    print("=" * 50 + "\n")

    # Generate evaluation_summary.txt
    summary_path = output_dir / "evaluation_summary.txt"
    with summary_path.open("w", encoding="utf-8") as f:
        f.write("==================================================\n")
        f.write("CHESS AI EVALUATION SUMMARY\n")
        f.write("==================================================\n")
        f.write(f"Total Games Processed:      {stats['total_games_processed']}\n")
        f.write(f"Total Positions Evaluated:  {total_pos}\n")
        f.write(f"Evaluation Duration:        {eval_duration_sec:.2f} seconds\n")
        f.write(f"Average Inference Time:     {avg_inf_time:.2f} ms\n")
        f.write(f"Average Legal Moves:        {avg_legal_moves:.1f}\n")
        f.write(f"Prediction Failures:        {stats['prediction_failures']}\n")
        f.write(f"Invalid Positions Skipped:  {stats['invalid_positions_skipped']}\n")
        f.write("--------------------------------------------------\n")
        f.write("ACCURACY METRICS:\n")
        f.write(f"  Top-1 Accuracy:  {top1_pct:.2f}%\n")
        f.write(f"  Top-3 Accuracy:  {top3_pct:.2f}%\n")
        f.write(f"  Top-5 Accuracy:  {top5_pct:.2f}%\n")
        f.write(f"  Top-10 Accuracy: {top10_pct:.2f}%\n")
        f.write("==================================================\n")
    print(f"Saved summary to: {summary_path.resolve()}")

    # Generate evaluation_report.md
    report_path = output_dir / "evaluation_report.md"
    with report_path.open("w", encoding="utf-8") as f:
        f.write("# Chess AI Playing Strength & Accuracy Evaluation Report\n\n")
        
        f.write("## Executive Summary\n")
        f.write(f"This report presents the play prediction accuracy and inference efficiency benchmarking of the Chess AI model across a test split of **{stats['total_games_processed']}** games, consisting of **{total_pos}** distinct positions.\n\n")
        
        f.write("### Key Metrics\n")
        f.write(f"- **Top-1 Accuracy**: {top1_pct:.2f}%\n")
        f.write(f"- **Top-3 Accuracy**: {top3_pct:.2f}%\n")
        f.write(f"- **Top-5 Accuracy**: {top5_pct:.2f}%\n")
        f.write(f"- **Top-10 Accuracy**: {top10_pct:.2f}%\n")
        f.write(f"- **Average Inference Speed**: {avg_inf_time:.2f} ms / position\n")
        f.write(f"- **Average Legal Moves / Board**: {avg_legal_moves:.1f}\n\n")
        
        f.write("## Detailed Game Phase Performance\n")
        f.write("Evaluating performance across game phases verifies the model's opening memory vs. middlegame tactical planning and endgame conversion capability.\n\n")
        f.write("| Phase | Positions | Top-1 Accuracy | Top-3 Accuracy | Top-5 Accuracy | Top-10 Accuracy |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: |\n")
        for phase in ("opening", "middlegame", "endgame"):
            p_data = stats["phases"][phase]
            p_count = p_data["count"]
            if p_count > 0:
                p_top1 = (p_data["top1"] / p_count) * 100
                p_top3 = (p_data["top3"] / p_count) * 100
                p_top5 = (p_data["top5"] / p_count) * 100
                p_top10 = (p_data["top10"] / p_count) * 100
                f.write(f"| {phase.capitalize()} (Moves {'1-10' if phase == 'opening' else '11-40' if phase == 'middlegame' else '41+'}) | {p_count} | {p_top1:.2f}% | {p_top3:.2f}% | {p_top5:.2f}% | {p_top10:.2f}% |\n")
            else:
                f.write(f"| {phase.capitalize()} | 0 | N/A | N/A | N/A | N/A |\n")
        f.write("\n")

        f.write("## Performance by Game Outcome\n")
        f.write("Analyzes move agreement with players based on the ultimate result of the game. High agreement in wins suggests alignment with strong winning paths.\n\n")
        f.write("| Outcome | Positions | Top-1 Accuracy | Top-3 Accuracy | Top-5 Accuracy | Top-10 Accuracy |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: |\n")
        for outcome_name, outcome_label in (("white_wins", "White Wins"), ("black_wins", "Black Wins"), ("draws", "Draws")):
            o_data = stats["outcomes"][outcome_name]
            o_count = o_data["count"]
            if o_count > 0:
                o_top1 = (o_data["top1"] / o_count) * 100
                o_top3 = (o_data["top3"] / o_count) * 100
                o_top5 = (o_data["top5"] / o_count) * 100
                o_top10 = (o_data["top10"] / o_count) * 100
                f.write(f"| {outcome_label} | {o_count} | {o_top1:.2f}% | {o_top3:.2f}% | {o_top5:.2f}% | {o_top10:.2f}% |\n")
            else:
                f.write(f"| {outcome_label} | 0 | N/A | N/A | N/A | N/A |\n")
        f.write("\n")
        
        f.write("## Execution & System Benchmarking\n")
        f.write(f"- **Inference Hardware Device**: `{inference.device}`\n")
        f.write(f"- **Total Time Spent on Eval**: {eval_duration_sec:.2f} seconds\n")
        f.write(f"- **Invalid Positions Skipped**: {stats['invalid_positions_skipped']}\n")
        f.write(f"- **Inference Failures Encountered**: {stats['prediction_failures']}\n")
        
    print(f"Saved report to: {report_path.resolve()}")

if __name__ == "__main__":
    main()
