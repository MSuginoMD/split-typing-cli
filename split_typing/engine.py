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


def score_attempt(expected: str, actual: str, seconds: float) -> Score:
    elapsed = max(seconds, 0.001)
    mismatches: list[tuple[int, str, str]] = []
    matches = 0

    for index, (want, got) in enumerate(zip_longest(expected, actual, fillvalue=""), start=1):
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
