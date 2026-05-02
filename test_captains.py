import csv
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from captains import CaptainSelector


def make_selector(rows=None):
    """Creates a CaptainSelector backed by a temp CSV. Returns (selector, path)."""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8", newline="")
    if rows:
        writer = csv.DictWriter(tmp, fieldnames=["Date", "Captain 1", "Captain 2", "Toss Winner"])
        writer.writeheader()
        writer.writerows(rows)
    tmp.close()
    return CaptainSelector(log_file=tmp.name), tmp.name


def silent_pick(selector):
    with patch("time.sleep"), patch("builtins.print"):
        return selector.pick_captains()


# --- load_history ---

class TestLoadHistory(unittest.TestCase):

    def test_no_file_gives_empty_state(self):
        s = CaptainSelector(log_file="nonexistent.csv")
        self.assertEqual(s.history, {})
        self.assertEqual(s.last_captains, set())

    def test_history_counts_correct(self):
        rows = [
            {"Date": "01-01-2026", "Captain 1": "Kabir", "Captain 2": "Dev",   "Toss Winner": "Kabir"},
            {"Date": "08-01-2026", "Captain 1": "Kabir", "Captain 2": "Soham", "Toss Winner": "Soham"},
        ]
        s, path = make_selector(rows)
        self.assertEqual(s.history["kabir"], 2)
        self.assertEqual(s.history["dev"], 1)
        self.assertEqual(s.history["soham"], 1)
        os.unlink(path)

    def test_last_captains_from_final_row(self):
        rows = [
            {"Date": "01-01-2026", "Captain 1": "Kabir", "Captain 2": "Dev",   "Toss Winner": "Kabir"},
            {"Date": "08-01-2026", "Captain 1": "Parth", "Captain 2": "Soham", "Toss Winner": "Parth"},
        ]
        s, path = make_selector(rows)
        self.assertEqual(s.last_captains, {"parth", "soham"})
        os.unlink(path)

    def test_corrupted_file_warns_and_gives_empty_state(self):
        # Write a CSV with wrong column names to trigger a KeyError in load_history
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8", newline="")
        tmp.write("Wrong,Headers,Here\nfoo,bar,baz\n")
        tmp.close()
        with patch("builtins.print") as mock_print:
            s = CaptainSelector(log_file=tmp.name)
        os.unlink(tmp.name)
        self.assertEqual(s.history, {})
        self.assertTrue(any("Could not read" in str(c) for c in mock_print.call_args_list))


# --- get_weight ---

class TestGetWeight(unittest.TestCase):

    def test_weight_is_inverse_of_count_plus_one(self):
        s = CaptainSelector(log_file="nonexistent.csv")
        self.assertEqual(s.get_weight("new_player"), 1.0)
        s.history["veteran"] = 4
        self.assertAlmostEqual(s.get_weight("veteran"), 0.2)


# --- get_players ---

class TestGetPlayers(unittest.TestCase):

    def _run(self, names):
        s = CaptainSelector(log_file="nonexistent.csv")
        with patch("builtins.input", side_effect=names + [""]), patch("builtins.print"):
            s.get_players()
        return s

    def test_names_lowercased_and_duplicates_removed(self):
        s = self._run(["Kabir", "Dev", "Kabir", "Parth"])
        self.assertEqual(s.players, ["kabir", "dev", "parth"])

    def test_duplicate_triggers_warning(self):
        s = CaptainSelector(log_file="nonexistent.csv")
        with patch("builtins.input", side_effect=["Kabir", "Dev", "Kabir", ""]), patch("builtins.print") as p:
            s.get_players()
        self.assertTrue(any("Duplicate" in str(c) for c in p.call_args_list))

    def test_fewer_than_two_players_exits(self):
        s = CaptainSelector(log_file="nonexistent.csv")
        with patch("builtins.input", side_effect=["Kabir", ""]), patch("builtins.print"):
            with self.assertRaises(SystemExit):
                s.get_players()


# --- pick_captains ---

class TestPickCaptains(unittest.TestCase):

    def _selector(self, players, last_captains=None):
        s = CaptainSelector(log_file="nonexistent.csv")
        s.players = players
        s.last_captains = last_captains or set()
        return s

    def test_returns_two_distinct_players_from_list(self):
        players = ["kabir", "dev", "parth", "soham", "kunal"]
        s = self._selector(players)
        for _ in range(20):
            c1, c2 = silent_pick(s)
            self.assertIn(c1, players)
            self.assertIn(c2, players)
            self.assertNotEqual(c1, c2)

    def test_last_captains_excluded(self):
        players = ["kabir", "dev", "parth", "soham", "kunal"]
        s = self._selector(players, last_captains={"kabir", "dev"})
        for _ in range(30):
            c1, c2 = silent_pick(s)
            self.assertNotIn(c1, {"kabir", "dev"})
            self.assertNotIn(c2, {"kabir", "dev"})

    def test_two_gks_pair_together(self):
        players = ["ronak gk", "jay gk", "kabir", "dev", "parth"]
        s = self._selector(players)
        with patch("random.choices", side_effect=[["ronak gk"], ["jay gk"]]), \
             patch("time.sleep"), patch("builtins.print"):
            c1, c2 = s.pick_captains()
        self.assertIn("gk", c1)
        self.assertIn("gk", c2)

    def test_single_gk_falls_back_to_outfield(self):
        players = ["ronak gk", "kabir", "dev", "parth", "soham"]
        s = self._selector(players)
        with patch("random.choices", side_effect=[["ronak gk"], ["kabir"], ["dev"]]), \
             patch("time.sleep"), patch("builtins.print"):
            c1, c2 = s.pick_captains()
        self.assertNotIn("gk", c1)
        self.assertNotIn("gk", c2)


# --- log_results ---

class TestLogResults(unittest.TestCase):

    def test_writes_correct_row_and_header(self):
        tmp = tempfile.mktemp(suffix=".csv")
        s = CaptainSelector(log_file=tmp)
        with patch("builtins.input", side_effect=["y", "03-05-2026"]), patch("builtins.print"):
            s.log_results("kabir", "dev", "kabir")
        with open(tmp, encoding="utf-8") as f:
            content = f.read()
        os.unlink(tmp)
        self.assertIn("Date,Captain 1,Captain 2,Toss Winner", content)
        self.assertIn("03-05-2026,Kabir,Dev,Kabir", content)

    def test_appends_without_duplicate_header(self):
        rows = [{"Date": "01-01-2026", "Captain 1": "Parth", "Captain 2": "Soham", "Toss Winner": "Parth"}]
        s, path = make_selector(rows)
        with patch("builtins.input", side_effect=["y", "08-01-2026"]), patch("builtins.print"):
            s.log_results("kabir", "dev", "dev")
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        os.unlink(path)
        self.assertEqual(sum(1 for l in lines if l.startswith("Date,")), 1)

    def test_invalid_date_reprompts(self):
        tmp = tempfile.mktemp(suffix=".csv")
        s = CaptainSelector(log_file=tmp)
        with patch("builtins.input", side_effect=["y", "2026-05-03", "03-05-2026"]), patch("builtins.print") as p:
            s.log_results("kabir", "dev", "kabir")
        os.unlink(tmp)
        self.assertTrue(any("Invalid" in str(c) for c in p.call_args_list))

    def test_no_file_written_on_decline(self):
        tmp = tempfile.mktemp(suffix=".csv")
        s = CaptainSelector(log_file=tmp)
        with patch("builtins.input", return_value="n"), patch("builtins.print"):
            s.log_results("kabir", "dev", "kabir")
        self.assertFalse(os.path.exists(tmp))


if __name__ == "__main__":
    unittest.main(verbosity=2)