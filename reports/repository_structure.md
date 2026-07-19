# Reorganized Repository Structure

This report documents the organized open-source folder layout of the **Supervised Chess AI** project.

---

```text
Hikaru/
├── .gitignore
├── LICENSE
├── README.md                          # Root-level project introduction
├── Main/
│   └── req.txt                        # System active requirements log
├── data/                              # Datasets and preprocessing tools
│   ├── splits/                        # Split datasets
│   │   ├── train.pgn                  # Training split (4,837 games, 423,469 samples)
│   │   ├── validation.pgn             # Validation split (604 games, 53,613 samples)
│   │   └── test.pgn                   # Test split (606 games, 54,041 samples)
│   ├── game-3K.pgn                    # Base dataset (3,000 games)
│   ├── pgn.py                         # Dataset split creation script (original)
│   └── more data/                     # Directory for new datasets
│       └── Malakhov.pgn               # Additional PGN dataset
├── src/                               # Active source codebase modules
│   ├── board_encoder.py               # Board state encoder
│   ├── move_encoder.py                # Move class encoder
│   ├── chess_model.py                 # ChessMoveCNN neural network model
│   ├── chess_dataset.py               # Dataset dataloader setup
│   ├── inference.py                   # Core inference engine API
│   ├── play_cli.py                    # Interactive console play CLI
│   ├── evaluate.py                    # PGN move evaluation utility
│   ├── train.py                       # Supervised training loop script
│   ├── verify_training_encoding.py    # Training set validation script
│   ├── extract_training_samples.py    # Split sample counting utility
│   └── promotion_analysis.py          # Promotion class index analyser
├── tests/                             # Unit testing suite
│   ├── test_move_encoder.py           # Move class coding verification
│   ├── test_pgn_split.py              # Disjoint split checks
│   ├── test_pgn_split_files.py        # File export verification
│   └── test_pgn_split_verification.py # Saved split checks
├── models/                            # Production trained models
│   ├── best_model.pth                 # Selected model (validation loss 4.0642)
│   ├── last_model.pth                 # Training end model
│   ├── checkpoint_info.txt            # Current model metadata
│   ├── training_summary.txt           # Current model training summary
│   └── archive/                       # Archive of previous models
│       └── 2026-07-18_15-03-14/       # Timestamped archive folder
│           ├── best_model.pth
│           ├── last_model.pth
│           ├── checkpoint_info.txt
│           └── training_summary.txt
├── docs/                              # Project documentation
│   ├── README.md                      # Copy of introduction file
│   ├── architecture.md                # System design & architecture details
│   └── roadmap.md                     # Future roadmap milestones
├── reports/                           # Historic logs and evaluation reports
│   ├── dataset_report.md              # Expanded dataset report
│   ├── phase_1_report.md              # Dataset analysis report
│   ├── phase_2_report.md              # Pipeline validation report
│   ├── phase_3_report.md              # Model training report
│   ├── phase_4_report.md              # Gameplay CLI report
│   ├── phase_5_report.md              # Benchmark evaluation report
│   ├── evaluation_report.md           # Detailed benchmark results
│   ├── evaluation_summary.txt         # Plaintext benchmark summary
│   ├── comparison_report.md           # Model playing strength comparison report
│   ├── step_4_verification_report.md  # Inference unit tests
│   ├── step_5_verification_report.md  # Decode unit tests
│   ├── step_6_verification_report.md  # Legality unit tests
│   ├── step_7_verification_report.md  # API pipeline unit tests
│   ├── step_8_verification_report.md  # Console game loop verification
│   └── archive/                       # Archive of previous reports
│       └── 2026-07-18_15-03-14/       # Timestamped report archive folder
│           ├── evaluation_report.md
│           ├── evaluation_summary.txt
│           ├── phase_1_report.md
│           ├── phase_2_report.md
│           ├── phase_3_report.md
│           ├── phase_4_report.md
│           ├── phase_5_report.md
│           ├── step_4_verification_report.md
│           ├── step_5_verification_report.md
│           ├── step_6_verification_report.md
│           ├── step_7_verification_report.md
│           └── step_8_verification_report.md
└── archive/                           # Historic session files
    ├── workflow.md                    # Initial plan outline
    ├── session_handoff.md             # Inter-run summary logs
    └── 2026-07-18_15-03-14/           # Previous training checkpoint archive
        ├── best_model.pth
        ├── last_model.pth
        ├── checkpoint_info.txt
        └── training_summary.txt
```
