import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock
from split_typing.stats import KeyStats
import split_typing.cli as cli
from split_typing.cli import (
    build_parser,
    print_weak_keys,
    print_realtime_summary,
    run_realtime_prompt,
    choose_language,
    choose_level,
    choose_count,
    choose_yes_no,
)


class TestCliPlumbing(unittest.TestCase):
    def test_new_flags_parse(self):
        args = build_parser().parse_args(
            ["--language", "english", "--level", "1", "--classic", "--adaptive"]
        )
        self.assertTrue(args.classic)
        self.assertTrue(args.adaptive)

    def test_stats_flag(self):
        args = build_parser().parse_args(["--stats"])
        self.assertTrue(args.stats)

    def test_no_color_flag(self):
        args = build_parser().parse_args(["--no-color"])
        self.assertTrue(args.no_color)

    def test_print_weak_keys_runs(self):
        s = KeyStats(Path("/tmp/unused.json"), {})
        s.record("z", 400.0, error=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            print_weak_keys(s)
        self.assertIn("z", buf.getvalue())

    def test_print_weak_keys_no_data(self):
        s = KeyStats(Path("/tmp/unused.json"), {})
        buf = io.StringIO()
        with redirect_stdout(buf):
            print_weak_keys(s)
        self.assertIn("No stats", buf.getvalue())


class TestInteractiveMenus(unittest.TestCase):
    def test_choose_language_by_number(self):
        with mock.patch("builtins.input", side_effect=["2"]), redirect_stdout(io.StringIO()):
            # second language in the catalog
            from split_typing.prompts import available_languages
            self.assertEqual(choose_language(), available_languages()[1])

    def test_choose_language_by_name(self):
        with mock.patch("builtins.input", side_effect=["japanese"]), redirect_stdout(io.StringIO()):
            self.assertEqual(choose_language(), "japanese")

    def test_choose_level_by_number(self):
        with mock.patch("builtins.input", side_effect=["3"]), redirect_stdout(io.StringIO()):
            self.assertEqual(choose_level("japanese"), 3)

    def test_choose_count_default_on_empty(self):
        with mock.patch("builtins.input", side_effect=[""]):
            self.assertEqual(choose_count(default=5), 5)

    def test_choose_count_number(self):
        with mock.patch("builtins.input", side_effect=["8"]):
            self.assertEqual(choose_count(default=5), 8)

    def test_choose_count_rejects_then_accepts(self):
        with mock.patch("builtins.input", side_effect=["0", "abc", "3"]), redirect_stdout(io.StringIO()):
            self.assertEqual(choose_count(default=5), 3)

    def test_choose_yes_no_default_and_answers(self):
        with mock.patch("builtins.input", side_effect=[""]):
            self.assertFalse(choose_yes_no("q", default=False))
        with mock.patch("builtins.input", side_effect=[""]):
            self.assertTrue(choose_yes_no("q", default=True))
        with mock.patch("builtins.input", side_effect=["y"]):
            self.assertTrue(choose_yes_no("q"))
        with mock.patch("builtins.input", side_effect=["n"]):
            self.assertFalse(choose_yes_no("q"))


class TestRealtimeSummary(unittest.TestCase):
    def test_summary_shows_counts_and_weak_keys(self):
        s = KeyStats(Path("/tmp/unused.json"), {})
        s.record("z", 400.0, error=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            print_realtime_summary(completed=2, total=3, errors=1, stats=s)
        out = buf.getvalue()
        self.assertIn("2/3", out)
        self.assertIn("z", out)


class TestKeystrokeRecording(unittest.TestCase):
    def test_ime_and_enter_not_recorded(self):
        # User left IME on (gets レ) and hit Enter (\r) before typing romaji.
        # Neither should land in stats; only the real ASCII keys for nihon do.
        stats = KeyStats(Path("/tmp/unused.json"), {})
        keys = ["レ", "\r", "n", "i", "h", "o", "n"]
        with mock.patch.object(cli, "read_keys", lambda: iter(keys)), redirect_stdout(io.StringIO()):
            sess = run_realtime_prompt("にほん", "にほん", stats, color=False)
        self.assertTrue(sess.done)
        self.assertNotIn("レ", stats.data)
        self.assertNotIn("\r", stats.data)
        self.assertIn("n", stats.data)
        self.assertIn("i", stats.data)


class TestResetStats(unittest.TestCase):
    def test_reset_stats_flag_parses(self):
        self.assertTrue(build_parser().parse_args(["--reset-stats"]).reset_stats)

    def test_reset_stats_clears_file(self):
        import json
        import split_typing.stats as stats_mod
        with TemporaryDirectory() as d:
            p = Path(d) / "stats.json"
            KeyStats(p, {"z": {"count": 1, "errors": 1, "total_ms": 9.0, "ema_ms": 9.0}}).save()
            with mock.patch.object(stats_mod, "DEFAULT_PATH", p), redirect_stdout(io.StringIO()):
                rc = cli.main(["--reset-stats"])
            self.assertEqual(rc, 0)
            self.assertEqual(json.loads(p.read_text()), {})


class TestRealtimeEntry(unittest.TestCase):
    def test_japanese_realtime_entry_does_not_crash(self):
        # Regression: a local var named `reading` once shadowed the reading
        # module, making the pykakasi guard raise UnboundLocalError on the
        # realtime Japanese path. Force that path with a fake TTY + key stream.
        with TemporaryDirectory() as d:
            stats_path = Path(d) / "stats.json"
            with mock.patch.object(cli, "supports_raw", lambda: True), \
                 mock.patch.object(cli, "read_keys", lambda: iter(["\x1b"])), \
                 mock.patch.object(KeyStats, "load", classmethod(lambda klass, path=None: KeyStats(stats_path, {}))), \
                 redirect_stdout(io.StringIO()):
                rc = cli.main(["--language", "japanese", "--level", "1", "--count", "1"])
        self.assertEqual(rc, 0)
