from __future__ import annotations

from dataclasses import dataclass
from itertools import zip_longest


@dataclass(frozen=True)
class Score:
    expected: str
    actual: str
    seconds: float
    accuracy: float
    errors: int
    wpm: float
    cpm: float
    mismatches: list[tuple[int, str, str]]


def _normalize(text: str) -> str:
    # Treat the IME full-width space (U+3000) as a normal space so Japanese
    # prompts typed with a kana IME aren't penalized for the space character.
    return text.replace("　", " ")


def score_attempt(expected: str, actual: str, seconds: float) -> Score:
    elapsed = max(seconds, 0.001)
    mismatches: list[tuple[int, str, str]] = []
    matches = 0

    norm_expected = _normalize(expected)
    norm_actual = _normalize(actual)
    for index, (want, got) in enumerate(zip_longest(norm_expected, norm_actual, fillvalue=""), start=1):
        if want == got:
            matches += 1
        else:
            mismatches.append((index, want, got))

    denominator = max(len(expected), len(actual), 1)
    accuracy = matches / denominator
    minutes = elapsed / 60.0
    cpm = len(actual) / minutes
    wpm = len(actual) / 5.0 / minutes

    return Score(
        expected=expected,
        actual=actual,
        seconds=elapsed,
        accuracy=round(accuracy, 4),
        errors=len(mismatches),
        wpm=round(wpm, 2),
        cpm=round(cpm, 2),
        mismatches=mismatches[:8],
    )


from split_typing.romaji import RomajiMatcher
from split_typing.stats import KeyStats


class RealtimeSession:
    def __init__(self, reading: str, stats: KeyStats | None = None) -> None:
        self.matcher = RomajiMatcher(reading)
        self.stats = stats
        self.errors = 0

    @property
    def done(self) -> bool:
        return self.matcher.done

    @property
    def typed(self) -> str:
        return self.matcher.typed

    @property
    def hint(self) -> str:
        return self.matcher.hint

    def key(self, ch: str, ms: float) -> str:
        result = self.matcher.feed(ch)
        if result == "wrong":
            self.errors += 1
        if self.stats is not None:
            self.stats.record(ch, ms, error=(result == "wrong"))
        return result

    def backspace(self) -> None:
        self.matcher.backspace()
