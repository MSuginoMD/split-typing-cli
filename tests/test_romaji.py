import unittest
from split_typing.romaji import tokenize_kana, romaji_variants, build_segments, RomajiMatcher


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


class TestBuildSegments(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(build_segments("か"), [["ka"]])

    def test_sokuon_doubles_next_consonant(self):
        # がっこう -> ga / っこ(=kko) / う
        segs = build_segments("がっこう")
        self.assertEqual(segs[0], ["ga"])
        self.assertIn("kko", segs[1])
        self.assertEqual(segs[2], ["u"])

    def test_n_keeps_bare_before_consonant(self):
        # にほん だ -> ...ん before space/da: bare n allowed
        segs = build_segments("ほんだ")
        n_seg = segs[1]
        self.assertIn("n", n_seg)
        self.assertIn("nn", n_seg)

    def test_n_drops_bare_before_vowel(self):
        # れんあい -> ん before あ(vowel): bare n NOT allowed
        segs = build_segments("れんあい")
        n_seg = segs[1]
        self.assertNotIn("n", n_seg)
        self.assertIn("nn", n_seg)


def _type(reading, text):
    m = RomajiMatcher(reading)
    results = [m.feed(c) for c in text]
    return m, results


class TestRomajiMatcher(unittest.TestCase):
    def test_simple_word(self):
        m, res = _type("にほん", "nihon")
        self.assertTrue(m.done)
        self.assertNotIn("wrong", res)
        self.assertEqual(m.typed, "nihon")

    def test_alt_spelling(self):
        m, _ = _type("し", "si")
        self.assertTrue(m.done)
        m2, _ = _type("し", "shi")
        self.assertTrue(m2.done)

    def test_double_n(self):
        m, _ = _type("れんあい", "rennai")
        self.assertTrue(m.done)

    def test_sokuon(self):
        m, _ = _type("がっこう", "gakkou")
        self.assertTrue(m.done)

    def test_wrong_char(self):
        m = RomajiMatcher("か")
        self.assertEqual(m.feed("x"), "wrong")
        self.assertFalse(m.done)
        self.assertEqual(m.feed("k"), "correct")
        self.assertEqual(m.feed("a"), "complete")
        self.assertTrue(m.done)

    def test_word_final_n_double(self):
        m, res = _type("にほん", "nihonn")
        self.assertTrue(m.done)
        self.assertNotIn("wrong", res)

    def test_standalone_n_double(self):
        m, res = _type("ん", "nn")
        self.assertTrue(m.done)
        self.assertNotIn("wrong", res)


class TestMatcherAux(unittest.TestCase):
    def test_backspace(self):
        m = RomajiMatcher("か")
        m.feed("k")
        self.assertTrue(m.backspace())
        self.assertEqual(m.typed, "")
        self.assertFalse(m.backspace())  # nothing to remove

    def test_expected_chars(self):
        m = RomajiMatcher("し")
        self.assertEqual(m.expected_chars, {"s"})  # shi / si both start with s

    def test_hint(self):
        m = RomajiMatcher("にほん")
        self.assertEqual(m.hint, "nihon")
        m.feed("n")
        m.feed("i")
        self.assertEqual(m.hint, "hon")
