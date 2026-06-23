import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from split_typing.stats import KeyStats
from split_typing.cli import build_parser, print_weak_keys


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
