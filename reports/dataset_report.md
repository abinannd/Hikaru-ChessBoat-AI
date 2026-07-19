# Supervised Chess AI — Merged Dataset Report

This report presents the details of the expanded, merged chess dataset used for training the supervised Chess AI engine.

---

## 📊 Dataset Executive Summary

The dataset was constructed by merging the original chess dataset with an additional high-quality chess game archive. All games have been parsed, validated, and filtered to ensure high-quality supervised-learning signals.

- **Total PGN Games Parsed**: 6,123
- **Total Accepted Games**: 6,047 (after ply-threshold filtering and deduplication)
- **Total Rejected Games**: 75
- **Total Duplicate Games Removed**: 1
- **Game result distribution**:
  - **White wins (`1-0`)**: 2,021 games (33.42%)
  - **Black wins (`0-1`)**: 1,314 games (21.73%)
  - **Draws (`1/2-1/2`)**: 2,712 games (44.85%)

---

## 📈 Detailed Statistics

### 1. Game Length (Ply Statistics)
Only games with 20 or more plies were accepted into the final dataset. Very short games (e.g., early resignations, draws by agreement) contain minimal tactical content and were excluded.

- **Minimum plies**: 20
- **Maximum plies**: 400
- **Mean plies**: 87.83
- **Median plies**: 82.00

### 2. Player Elo Ratings
Player ratings were reviewed to verify that the dataset represents master-level chess play.

- **Minimum player Elo**: 1,382
- **Maximum player Elo**: 2,865
- **Mean player Elo**: 2,616.51
- **Median player Elo**: 2,658.00

---

## 📂 Dataset Splits & Isolation

An **80/10/10** game-level split was performed using a fixed random seed of `42` to ensure complete reproducibility. Splitting at the game level prevents data leakage between splits.

| Split | Games | Positions (Samples) | Purpose |
|---|:---:|:---:|---|
| **Training** | 4,837 | 423,469 | Model parameters optimization |
| **Validation** | 604 | 53,613 | Hyperparameters tuning and early stopping monitoring |
| **Test** | 606 | 54,041 | Final playing strength evaluation |
| **Combined** | **6,047** | **531,123** | |

### Verification Checks Passed:
1. **Overlap Check**: Training, validation, and test datasets have completely disjoint sets of games (No overlap = **True**).
2. **PGN Integrity Check**: All splits read back and parsed successfully using `python-chess` without errors.
3. **Move Encodings Check**: All 531,123 positions were checked for shape `(18, 8, 8)` and legal move class index `0-4271` without a single failure.
