# Reorganized Repository Structure

This report documents the organized open-source folder layout of the **Supervised Chess AI** project.

---

```text
Hikaru/
├── .gitignore
├── LICENSE
├── README.md                          # Root-level project introduction
├── Main/
│   ├── req.txt                        # System active requirements log
│   └── gui/                           # Kivy GUI frontend
│       ├── app.py                     # GUI entry point
│       ├── main_window.py             # Root vertical window (Header, Side panel, Status, AI move executor, Scrollable history & Undo/Redo controls)
│       ├── chess_board.py             # Chess board widget (8x8 squares with selection, highlights, move execution, board lock & interaction lock)
│       ├── chess_piece.py             # Chess piece widget (responsive unicode/image loader)
│       ├── assets/                    # Static graphical assets
│       │   ├── pieces/                # Chess pieces images (placeholder)
│       │   ├── boards/                # Chess board images (placeholder)
│       │   └── icons/                 # UI icons (placeholder)
│       ├── screens/                   # UI screen placeholders
│       ├── widgets/                   # Custom UI widget placeholders
│       ├── themes/                    # Graphical theme settings
│       └── utils/                     # UI math and coordinate helpers
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
│   ├── phase7_step1_verification.md   # Kivy GUI layout verification report
│   ├── phase7_step2_verification.md   # Responsive Chessboard rendering report
│   ├── phase7_step3_piece_rendering.md# Chess piece rendering verification report
│   ├── phase7_step4_verification.md   # User interaction & piece selection report
│   ├── phase7_step5_verification.md   # Legal move highlighting report
│   ├── phase7_step6_verification.md   # Human move execution report
│   ├── phase7_step7_verification.md   # Game state management report
│   ├── phase8_step1_verification.md   # Chess AI engine integration report
│   ├── phase8_step2_verification.md   # Human vs AI gameplay loop report
│   ├── phase9_step1_verification.md   # Move history panel (SAN/PGN) report
│   ├── phase9_step2_verification.md   # Undo / Redo system report
│   ├── step_4_verification_report.md  # Inference unit tests
│   ├── step_5_verification_report.md  # Decode unit tests
│   ├── step_6_verification_report.md  # Legal move check unit tests
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
