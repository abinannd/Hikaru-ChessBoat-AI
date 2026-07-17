import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from data.pgn import create_split_sets


class PgnSplitTests(unittest.TestCase):
    def test_split_sets_are_disjoint_and_sizes_match(self):
        games = [f"game-{idx}" for idx in range(3736)]

        train_games, val_games, test_games = create_split_sets(games)

        self.assertEqual(len(train_games), 2988)
        self.assertEqual(len(val_games), 374)
        self.assertEqual(len(test_games), 374)
        self.assertEqual(len(train_games) + len(val_games) + len(test_games), len(games))

        train_ids = {id(game) for game in train_games}
        val_ids = {id(game) for game in val_games}
        test_ids = {id(game) for game in test_games}

        self.assertTrue(train_ids.isdisjoint(val_ids))
        self.assertTrue(train_ids.isdisjoint(test_ids))
        self.assertTrue(val_ids.isdisjoint(test_ids))


if __name__ == "__main__":
    unittest.main()
