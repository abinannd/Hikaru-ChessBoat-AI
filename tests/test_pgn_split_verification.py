import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from data.pgn import verify_saved_split_files


class PgnSplitVerificationTests(unittest.TestCase):
    def test_verify_saved_split_files_returns_expected_counts(self):
        split_dir = Path(__file__).resolve().parent.parent / "data" / "splits"
        results = verify_saved_split_files(split_dir)

        self.assertIn("train", results)
        self.assertIn("validation", results)
        self.assertIn("test", results)
        self.assertEqual(results["train"]["expected"], 2988)
        self.assertEqual(results["validation"]["expected"], 374)
        self.assertEqual(results["test"]["expected"], 374)


if __name__ == "__main__":
    unittest.main()
