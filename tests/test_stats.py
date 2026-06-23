import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from split_typing.stats import KeyStats


class TestKeyStatsIO(unittest.TestCase):
    def test_missing_file_is_empty(self):
        with TemporaryDirectory() as d:
            s = KeyStats.load(Path(d) / "nope.json")
            self.assertEqual(s.data, {})

    def test_roundtrip(self):
        with TemporaryDirectory() as d:
            p = Path(d) / "stats.json"
            s = KeyStats.load(p)
            s.data["k"] = {"count": 1, "errors": 0, "total_ms": 10.0, "ema_ms": 10.0}
            s.save()
            again = KeyStats.load(p)
            self.assertEqual(again.data["k"]["count"], 1)


class TestKeyStatsScoring(unittest.TestCase):
    def _fresh(self):
        from pathlib import Path
        return KeyStats(Path("/tmp/unused.json"), {})

    def test_record_updates(self):
        s = self._fresh()
        s.record("a", 120.0, error=False)
        self.assertEqual(s.data["a"]["count"], 1)
        self.assertEqual(s.data["a"]["errors"], 0)
        self.assertAlmostEqual(s.data["a"]["ema_ms"], 120.0)

    def test_weakness_orders_by_error_and_latency(self):
        s = self._fresh()
        for _ in range(10):
            s.record("good", 80.0, error=False)
        for _ in range(10):
            s.record("bad", 400.0, error=True)
        self.assertGreater(s.weakness("bad"), s.weakness("good"))
        self.assertEqual(s.weakest(1), ["bad"])

    def test_unseen_is_zero(self):
        self.assertEqual(self._fresh().weakness("z"), 0.0)
