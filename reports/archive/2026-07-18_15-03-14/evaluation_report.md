# Chess AI Playing Strength & Accuracy Evaluation Report

## Executive Summary
This report presents the play prediction accuracy and inference efficiency benchmarking of the Chess AI model across a test split of **374** games, consisting of **31444** distinct positions.

### Key Metrics
- **Top-1 Accuracy**: 18.02%
- **Top-3 Accuracy**: 30.14%
- **Top-5 Accuracy**: 36.81%
- **Top-10 Accuracy**: 46.50%
- **Average Inference Speed**: 2.02 ms / position
- **Average Legal Moves / Board**: 31.4

## Detailed Game Phase Performance
Evaluating performance across game phases verifies the model's opening memory vs. middlegame tactical planning and endgame conversion capability.

| Phase | Positions | Top-1 Accuracy | Top-3 Accuracy | Top-5 Accuracy | Top-10 Accuracy |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Opening (Moves 1-10) | 7480 | 47.25% | 69.51% | 78.93% | 88.45% |
| Middlegame (Moves 11-40) | 18379 | 10.10% | 19.36% | 25.05% | 34.43% |
| Endgame (Moves 41+) | 5585 | 4.92% | 12.87% | 19.09% | 30.06% |

## Performance by Game Outcome
Analyzes move agreement with players based on the ultimate result of the game. High agreement in wins suggests alignment with strong winning paths.

| Outcome | Positions | Top-1 Accuracy | Top-3 Accuracy | Top-5 Accuracy | Top-10 Accuracy |
| :--- | :---: | :---: | :---: | :---: | :---: |
| White Wins | 10562 | 17.57% | 29.04% | 35.40% | 45.21% |
| Black Wins | 6779 | 15.55% | 27.13% | 33.68% | 42.87% |
| Draws | 14103 | 19.53% | 32.41% | 39.37% | 49.22% |

## Execution & System Benchmarking
- **Inference Hardware Device**: `cuda`
- **Total Time Spent on Eval**: 105.13 seconds
- **Invalid Positions Skipped**: 0
- **Inference Failures Encountered**: 0
