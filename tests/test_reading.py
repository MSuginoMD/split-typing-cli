import unittest
from split_typing import reading


class TestReading(unittest.TestCase):
    def test_available_flag_is_bool(self):
        self.assertIsInstance(reading.pykakasi_available(), bool)

    @unittest.skipUnless(reading.pykakasi_available(), "pykakasi not installed")
    def test_converts_kanji(self):
        self.assertEqual(reading.to_hiragana("日本語"), "にほんご")

    def test_degrades_without_crash(self):
        # passing plain hiragana should round-trip regardless of pykakasi
        self.assertEqual(reading.to_hiragana("ねこ"), "ねこ")
