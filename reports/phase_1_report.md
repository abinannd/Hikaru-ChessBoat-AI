<div align="center">

# ♟️ Supervised Chess AI — Dataset Pipeline

### Phase 1 · Dataset Preparation (Updated)

*A clean, reproducible pipeline for turning raw PGN archives into training-ready chess data.*

![Status](https://img.shields.io/badge/status-complete-brightgreen)
![Games](https://img.shields.io/badge/games-6%2C047-blue)
![Tests](https://img.shields.io/badge/tests-9%20passed-success)
![Python](https://img.shields.io/badge/python-chess-informational)
![Seed](https://img.shields.io/badge/seed-42-lightgrey)

</div>

---

##  Table of Contents

1. [Overview](#-overview)
2. [Pipeline at a Glance](#-pipeline-at-a-glance)
3. [Dataset Inspection](#-1-initial-dataset-inspection)
4. [Game Result Analysis](#-2-game-result-analysis)
5. [Game Length Analysis](#️-3-game-length-analysis)
6. [Dataset Filtering](#-4-dataset-filtering)
7. [Player Elo Analysis](#-5-player-elo-analysis)
8. [Dataset Shuffling](#-6-dataset-shuffling)
9. [Train / Validation / Test Split](#-7-train--validation--test-split)
10. [Split Isolation Verification](#-8-split-isolation-verification)
11. [Saving the Dataset](#-9-saving-the-dataset-splits)
12. [Saved Dataset Verification](#-10-saved-dataset-verification)
13. [Regression Testing](#-11-regression-testing)
14. [Final Summary](#-phase-1-final-summary)

---

##  Overview

Phase 1 focuses on preparing a clean, reliable, and reproducible **chess game dataset** for training a supervised-learning chess AI.

The source dataset is constructed by merging the original chess dataset with an additional high-quality chess game archive. Before any of it touches a model, every game is **inspected → analyzed → filtered → shuffled → split → saved → verified**, with automated tests guarding the whole process.

> **What's a "ply"?** One move by one player. `1. e4 e5` = 2 plies (one white, one black).

---

##  Pipeline at a Glance

```mermaid
flowchart TD
    A["Original & Malakhov PGNs<br/>6,123 games"] --> B["PGN Parsing & Inspection"]
    B --> C["Game Result Analysis"]
    C --> D["Game Length Analysis"]
    D --> E["Dataset Filtering & Deduplication<br/><small>remove games &lt; 20 plies & duplicates</small>"]
    E --> F["6,047 unique accepted games"]
    F --> G["Elo Analysis"]
    G --> H["Random Shuffle<br/><small>seed = 42</small>"]
    H --> I["Game-Level Split (80/10/10)"]
    I --> J["Train<br/>4,837 games"]
    I --> K["Validation<br/>604 games"]
    I --> L["Test<br/>606 games"]
    J --> M["Read-Back Verification"]
    K --> M
    L --> M
    M --> N["✅ Phase 1 Complete"]

    style A fill:#1f2937,stroke:#4b5563,color:#fff
    style N fill:#065f46,stroke:#10b981,color:#fff
    style E fill:#7c2d12,stroke:#ea580c,color:#fff
    style H fill:#1e3a8a,stroke:#3b82f6,color:#fff
```

---

##  1. Initial Dataset Inspection

The PGN datasets were parsed using `python-chess` to confirm that games, player metadata, results, and move sequences could all be extracted correctly.

| Metric | Result |
|---|---:|
| Total games parsed | **6,123** |
| Shortest game parsed | 0 plies |
| Longest game parsed | 400 plies |
| Average game length | 87.83 plies |
| Games with fewer than 20 plies | 75 |

---

##  2. Game Result Analysis

Every result header across all games was checked for completeness.

| Game Result | Games | Share |
|---|---:|---:|
| White wins (`1-0`) | 2,021 | 33.42% |
| Black wins (`0-1`) | 1,314 | 21.73% |
| Draws (`1/2-1/2`) | 2,712 | 44.85% |
| Unknown / Other | 0 | 0.00% |
| **Total** | **6,047** | **100%** |

✅ All unique accepted games contained valid result information.

---

##  3. Game Length Analysis

Very short games carry little useful board-position/move-pair signal for supervised learning, so game lengths were bucketed and inspected.

| Game Length | Number of Games |
|---|---:|
| < 20 plies | 75 |
| 20+ plies | 6,048 |
| **Total** | **6,123** |

- **75 games** fell below the 20-ply threshold and were rejected.
- **1 duplicate game** was detected and removed.
- **6,047 unique accepted games** were retained.

---

##  4. Dataset Filtering

**Rule applied:** only unique games with **20 or more plies** are accepted into the ML dataset.

| Dataset Status | Games |
|---|---:|
| ✅ Accepted (20+ plies, unique) | 6,047 |
| ❌ Rejected (< 20 plies) | 75 |
| ❌ Duplicate Removed | 1 |
| **Original Parsed** | **6,123** |

---

##  5. Player Elo Analysis

Player ratings were reviewed to understand the playing strength represented in the data.

| Elo Metric | Result |
|---|---:|
| Minimum available Elo | 1,382 |
| Maximum available Elo | 2,865 |
| Average available Elo | 2,616.51 |
| Median available Elo | 2,658.00 |

The high average Elo confirms this is master-level chess play.

---

##  6. Dataset Shuffling

After filtering, **6,047 unique accepted games** remained and were randomly shuffled prior to splitting.

```
Random seed = 42
```

A fixed seed guarantees the split is **fully reproducible**.

---

##  7. Train / Validation / Test Split

An **80 / 10 / 10** split was applied **at the game level** (not per-position), so every position from a given game stays together in one bucket.

| Dataset | Games | Purpose |
|---|---:|---|
| 🟩 Training | 4,837 | Train the neural network |
| 🟨 Validation | 604 | Monitor performance and early stopping |
| 🟦 Testing | 606 | Final evaluation on unseen games |
| **Total** | **6,047** | |

---

##  8. Split Isolation Verification

| Check | Result |
|---|---|
| Training ↔ Validation overlap | None |
| Training ↔ Test overlap | None |
| Validation ↔ Test overlap | None |
| **Overall overlap check** | **✅ Passed** |

---

##  9. Saving the Dataset Splits

Each split was saved as an independent PGN file:

```text
data/
└── splits/
    ├── train.pgn
    ├── validation.pgn
    └── test.pgn
```

| File | Games |
|---|---:|
| `train.pgn` | 4,837 |
| `validation.pgn` | 604 |
| `test.pgn` | 606 |

---

##  10. Saved Dataset Verification

Each saved file was reopened and re-parsed to confirm game counts match exactly.

| PGN File | Expected | Read Back | Verification |
|---|---:|---:|---|
| `train.pgn` | 4,837 | 4,837 | ✅ Passed |
| `validation.pgn` | 604 | 604 | ✅ Passed |
| `test.pgn` | 606 | 606 | ✅ Passed |

---

##  11. Regression Testing

Automated tests guard the pipeline against regressions, covering:
- Correct dataset filtering
- Correct train / validation / test sizes
- No overlap between splits
- Correct PGN saving
- Correct PGN read-back

```text
9 passed
```

---

## ✅ Phase 1 Final Summary

<details>
<summary><strong>Click to expand full checklist</strong></summary>

- [x] Parsed successfully
- [x] Inspected for game results
- [x] Analyzed for game lengths
- [x] Analyzed for player Elo
- [x] Filtered to remove games with fewer than 20 plies
- [x] Randomly shuffled using a reproducible seed (`42`)
- [x] Split at the game level (80/10/10)
- [x] Checked for overlap between splits
- [x] Saved into separate PGN files
- [x] Read back and verified
- [x] Protected by regression tests

</details>
