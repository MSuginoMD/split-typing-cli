import unittest

from split_typing.prompts import available_languages, get_prompts, levels_for_language


class PromptTests(unittest.TestCase):
    def test_available_languages_are_separate_tracks(self):
        self.assertEqual(available_languages(), ("english", "japanese", "python"))

    def test_levels_are_one_through_four(self):
        self.assertEqual(levels_for_language("english"), (1, 2, 3, 4))
        self.assertEqual(levels_for_language("japanese"), (1, 2, 3, 4))
        self.assertEqual(levels_for_language("python"), (1, 2, 3, 4))

    def test_get_prompts_returns_requested_count_deterministically(self):
        prompts = get_prompts("english", 1, count=3, seed=7)
        self.assertEqual(len(prompts), 3)
        self.assertEqual(prompts, get_prompts("english", 1, count=3, seed=7))

    def test_invalid_language_raises_clear_error(self):
        with self.assertRaisesRegex(ValueError, "language"):
            get_prompts("latin", 1, count=1)

    def test_invalid_level_raises_clear_error(self):
        with self.assertRaisesRegex(ValueError, "level"):
            get_prompts("python", 9, count=1)


if __name__ == "__main__":
    unittest.main()
