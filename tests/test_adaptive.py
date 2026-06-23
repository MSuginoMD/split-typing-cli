import unittest
from pathlib import Path
from split_typing.stats import KeyStats
from split_typing.adaptive import prompt_weak_key_load, select_adaptive


def _stats_weak_on(keys):
    s = KeyStats(Path("/tmp/unused.json"), {})
    for k in keys:
        for _ in range(10):
            s.record(k, 400.0, error=True)
    return s


class TestAdaptive(unittest.TestCase):
    def test_load_counts_weak_keys(self):
        # english: prompt text == romaji
        self.assertEqual(prompt_weak_key_load("zzz aaa", "english", {"z"}), 3)

    def test_select_biases_to_weak(self):
        stats = _stats_weak_on(["z"])
        prompts = ["aaaa", "zzzz", "aaaa", "aaaa"]
        picks = select_adaptive(prompts, "english", stats, count=4, seed=1)
        self.assertIn("zzzz", picks)

    def test_deterministic(self):
        stats = _stats_weak_on(["z"])
        prompts = ["aaaa", "zzzz", "bbbb", "cccc"]
        a = select_adaptive(prompts, "english", stats, 3, seed=7)
        b = select_adaptive(prompts, "english", stats, 3, seed=7)
        self.assertEqual(a, b)
