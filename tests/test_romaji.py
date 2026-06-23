import unittest
from split_typing.romaji import tokenize_kana, romaji_variants


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


class TestRomajiVariants(unittest.TestCase):
    def test_multi_variant(self):
        self.assertIn("shi", romaji_variants("し"))
        self.assertIn("si", romaji_variants("し"))

    def test_youon(self):
        self.assertIn("kya", romaji_variants("きゃ"))

    def test_particle_choices_present(self):
        self.assertIn("wo", romaji_variants("を"))

    def test_passthrough(self):
        self.assertEqual(romaji_variants(" "), [" "])
        self.assertEqual(romaji_variants("、"), ["、"])

    def test_dji_youon_present(self):
        self.assertEqual(romaji_variants("ぢゃ"), ["dya", "jya"])

    def test_chi_youon_has_cya(self):
        self.assertIn("cya", romaji_variants("ちゃ"))
