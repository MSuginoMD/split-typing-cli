import unittest
from split_typing.romaji import tokenize_kana


class TestTokenizeKana(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(tokenize_kana("にほん"), ["に", "ほ", "ん"])

    def test_youon_is_one_unit(self):
        self.assertEqual(tokenize_kana("きゃく"), ["きゃ", "く"])

    def test_sokuon_is_own_unit(self):
        self.assertEqual(tokenize_kana("がっこう"), ["が", "っ", "こ", "う"])

    def test_katakana_normalized_but_choon_kept(self):
        self.assertEqual(tokenize_kana("テーブル"), ["て", "ー", "ぶ", "る"])

    def test_passthrough(self):
        self.assertEqual(tokenize_kana("あ、 a"), ["あ", "、", " ", "a"])
