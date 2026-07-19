# Chess AI Playing Strength & Accuracy Evaluation Report

## Executive Summary
This report presents the play prediction accuracy and inference efficiency benchmarking of the Chess AI model across a test split of **606** games, consisting of **54041** distinct positions.

### Key Metrics
- **Top-1 Accuracy**: 18.41%
- **Top-3 Accuracy**: 32.26%
- **Top-5 Accuracy**: 39.43%
- **Top-10 Accuracy**: 49.87%
- **Average Inference Speed**: 1.81 ms / position
- **Average Legal Moves / Board**: 30.7

## Detailed Game Phase Performance
Evaluating performance across game phases verifies the model's opening memory vs. middlegame tactical planning and endgame conversion capability.

| Phase | Positions | Top-1 Accuracy | Top-3 Accuracy | Top-5 Accuracy | Top-10 Accuracy |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Opening (Moves 1-10) | 12120 | 45.77% | 72.47% | 81.83% | 89.48% |
| Middlegame (Moves 11-40) | 31188 | 11.56% | 21.94% | 28.20% | 38.96% |
| Endgame (Moves 41+) | 10733 | 7.44% | 16.85% | 24.17% | 36.84% |

## Performance by Game Outcome
Analyzes move agreement with players based on the ultimate result of the game. High agreement in wins suggests alignment with strong winning paths.

| Outcome | Positions | Top-1 Accuracy | Top-3 Accuracy | Top-5 Accuracy | Top-10 Accuracy |
| :--- | :---: | :---: | :---: | :---: | :---: |
| White Wins | 17762 | 18.25% | 31.42% | 38.58% | 48.61% |
| Black Wins | 13301 | 16.83% | 29.99% | 37.27% | 48.15% |
| Draws | 22978 | 19.46% | 34.23% | 41.33% | 51.84% |

## Execution & System Benchmarking
- **Inference Hardware Device**: `cuda`
- **Total Time Spent on Eval**: 161.91 seconds
- **Invalid Positions Skipped**: 0
- **Inference Failures Encountered**: 0
