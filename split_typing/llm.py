from __future__ import annotations

import re
import subprocess


# Matches ANSI/VT escape sequences that ollama leaks into stdout while it
# live-renders streaming output (cursor moves, line clears, spinners).
_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b[=>]")

# ollama word-wraps streamed output at its own width. At a wrap it prints a few
# chars of the next word, backs the cursor up N columns (ESC[ND), clears to end
# of line (ESC[K) and reprints the whole word on a new line. This collapses that
# soft wrap back into one continuous line: drop the N pre-wrap chars, the escape
# sequence, and the inserted newline.
_SOFTWRAP_RE = re.compile(r"(?:\x1b\[(\d+)D)?\x1b\[K\n?")


def _clean_stream(text: str) -> str:
    while True:
        match = _SOFTWRAP_RE.search(text)
        if not match:
            break
        back = int(match.group(1) or 0)
        start = max(0, match.start() - back)
        text = text[:start] + text[match.end():]
    return _ANSI_RE.sub("", text)


def _dedup_key(line: str) -> str:
    """Normalize a line so near-identical prompts collapse to one key."""
    lowered = line.casefold()
    return re.sub(r"\s+", " ", lowered).strip()


def parse_generated_lines(text: str, count: int) -> list[str]:
    prompts: list[str] = []
    seen: set[str] = set()
    for raw in _clean_stream(text).splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"^[-*]\s+", "", line)
        line = re.sub(r"^\d+[.)]\s+", "", line)
        line = line.strip().strip("`").strip()
        if not line:
            continue
        key = _dedup_key(line)
        if key in seen:
            continue
        seen.add(key)
        prompts.append(line)
        if len(prompts) >= count:
            break
    return prompts


def generate_prompts(language: str, level: int, count: int, model: str = "gemma4:26b") -> list[str]:
    # Over-fetch so that, after dropping duplicates, we still have enough distinct
    # prompts to reach `count`.
    overfetch = count + max(count, 5)
    request = (
        "Create typing practice prompts for a local CLI typing trainer.\n"
        f"Language track: {language}\n"
        f"Difficulty level: {level} where 1 is short words and 4 is longer text.\n"
        f"Return exactly {overfetch} plain lines. No numbering, no markdown, no explanation.\n"
        "Every line must be DISTINCT: vary the vocabulary, topic, sentence shape, and "
        "starting word. Do not reuse the same phrases or restate the same idea across lines.\n"
        "Make prompts useful for adapting to a split keyboard. Keep each line typeable in a terminal."
    )
    try:
        completed = subprocess.run(
            # --think=false suppresses chain-of-thought output from reasoning
            # models (e.g. gemma4:26b); without it the thinking text leaks into
            # stdout and gets parsed as bogus prompts.
            ["ollama", "run", model, "--think=false", request],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return []
    return parse_generated_lines(completed.stdout, count)
