import subprocess
import unittest
from unittest.mock import patch

from split_typing.llm import build_request, generate_prompts, parse_generated_lines


class LlmTests(unittest.TestCase):
    def test_parse_generated_lines_removes_bullets_and_limits_count(self):
        text = """
        1. hello world
        - type slowly
        `print("ok")`
        extra line
        """

        self.assertEqual(
            parse_generated_lines(text, count=3),
            ["hello world", "type slowly", 'print("ok")'],
        )

    def test_parse_generated_lines_drops_duplicates(self):
        text = "type slowly\nType  Slowly\ntype slowly\nquick fox\n"

        self.assertEqual(
            parse_generated_lines(text, count=5),
            ["type slowly", "quick fox"],
        )

    def test_parse_generated_lines_repairs_ollama_softwrap(self):
        # ollama backs the cursor up and reprints a word when it wraps a line.
        text = "Developers utilize command-line automat\x1b[7D\x1b[K\nautomation daily.\n"

        self.assertEqual(
            parse_generated_lines(text, count=5),
            ["Developers utilize command-line automation daily."],
        )

    @patch("split_typing.llm.subprocess.run")
    def test_generate_prompts_calls_ollama(self, run):
        run.return_value = subprocess.CompletedProcess(
            args=["ollama"], returncode=0, stdout="alpha\nbeta\ngamma\n", stderr=""
        )

        prompts = generate_prompts("english", 2, 2, "gemma4")

        self.assertEqual(prompts, ["alpha", "beta"])
        self.assertIn("gemma4", run.call_args.args[0])

    @patch("split_typing.llm.subprocess.run", side_effect=OSError("missing"))
    def test_generate_prompts_returns_empty_list_on_failure(self, run):
        self.assertEqual(generate_prompts("python", 3, 4, "gemma4"), [])


class TestBuildRequest(unittest.TestCase):
    def test_japanese_request_asks_for_natural(self):
        req = build_request("japanese", 3, 10)
        self.assertIn("Japanese", req)
        self.assertIn("10", req)

    def test_english_request(self):
        req = build_request("english", 1, 8)
        self.assertIn("8", req)


if __name__ == "__main__":
    unittest.main()
