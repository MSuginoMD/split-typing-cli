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
