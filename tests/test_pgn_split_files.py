import sys
import unittest
from pathlib import Path
import tempfile

sys.path.append(str(Path(__file__).resolve().parent.parent))

from data.pgn import write_split_files


class PgnSplitFilesTests(unittest.TestCase):
    def test_write_split_files_writes_expected_count_and_returns_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            train_games = ["train-1", "train-2"]
            val_games = ["val-1"]
            test_games = ["test-1"]

            paths = write_split_files(output_dir, train_games, val_games, test_games)

            self.assertEqual(paths["train"].name, "train.pgn")
            self.assertEqual(paths["validation"].name, "validation.pgn")
            self.assertEqual(paths["test"].name, "test.pgn")
            self.assertTrue(paths["train"].exists())
            self.assertTrue(paths["validation"].exists())
            self.assertTrue(paths["test"].exists())

            self.assertEqual(paths["train"].read_text(encoding="utf-8"), "train-1\ntrain-2\n")
            self.assertEqual(paths["validation"].read_text(encoding="utf-8"), "val-1\n")
            self.assertEqual(paths["test"].read_text(encoding="utf-8"), "test-1\n")


if __name__ == "__main__":
    unittest.main()
