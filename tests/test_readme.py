import unittest
from pathlib import Path


class TestReadme(unittest.TestCase):
    def test_no_personal_paths(self):
        text = Path("README.md").read_text(encoding="utf-8")
        self.assertNotIn("/Users/", text)

    def test_mentions_key_features(self):
        text = Path("README.md").read_text(encoding="utf-8").lower()
        for token in ("realtime", "adaptive", "pykakasi", "classic"):
            self.assertIn(token, text)
