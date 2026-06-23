import unittest

from split_typing.engine import score_attempt


class EngineTests(unittest.TestCase):
    def test_exact_match_scores_full_accuracy(self):
        result = score_attempt("split", "split", seconds=6.0)

        self.assertEqual(result.accuracy, 1.0)
        self.assertEqual(result.errors, 0)
        self.assertEqual(result.wpm, 10.0)
        self.assertEqual(result.cpm, 50.0)

    def test_typo_reports_first_mismatches(self):
        result = score_attempt("split", "spilt", seconds=3.0)

        self.assertEqual(result.errors, 2)
        self.assertEqual(result.mismatches[:2], [(3, "l", "i"), (4, "i", "l")])
        self.assertAlmostEqual(result.accuracy, 0.6)

    def test_empty_input_scores_zero_accuracy(self):
        result = score_attempt("abc", "", seconds=1.0)

        self.assertEqual(result.accuracy, 0.0)
        self.assertEqual(result.errors, 3)
        self.assertEqual(result.mismatches, [(1, "a", ""), (2, "b", ""), (3, "c", "")])

    def test_extra_input_counts_as_errors(self):
        result = score_attempt("abc", "abcd", seconds=1.0)

        self.assertEqual(result.errors, 1)
        self.assertEqual(result.mismatches, [(4, "", "d")])

    def test_fullwidth_space_matches_halfwidth(self):
        result = score_attempt("みないで うつ", "みないで　うつ", seconds=1.0)

        self.assertEqual(result.accuracy, 1.0)
        self.assertEqual(result.errors, 0)
        self.assertEqual(result.mismatches, [])

    def test_zero_seconds_is_clamped_for_speed(self):
        result = score_attempt("abcde", "abcde", seconds=0.0)

        self.assertGreater(result.wpm, 0)
        self.assertGreater(result.cpm, 0)


from pathlib import Path
from split_typing.engine import RealtimeSession
from split_typing.stats import KeyStats


class TestRealtimeSession(unittest.TestCase):
    def test_completes_and_counts_errors(self):
        s = KeyStats(Path("/tmp/unused.json"), {})
        sess = RealtimeSession("か", stats=s)
        self.assertEqual(sess.key("x", 100.0), "wrong")
        self.assertEqual(sess.key("k", 90.0), "correct")
        self.assertEqual(sess.key("a", 80.0), "complete")
        self.assertTrue(sess.done)
        self.assertEqual(sess.errors, 1)
        self.assertEqual(s.data["x"]["errors"], 1)
        self.assertEqual(s.data["k"]["errors"], 0)


if __name__ == "__main__":
    unittest.main()
