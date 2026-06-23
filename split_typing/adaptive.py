from __future__ import annotations

import random

from split_typing.reading import to_hiragana
from split_typing.romaji import build_segments
from split_typing.stats import KeyStats


def _to_romaji(prompt: str, language: str) -> str:
    if language == "japanese":
        reading = to_hiragana(prompt)
        return "".join(seg[0] for seg in build_segments(reading))
    return prompt  # english / python: literal text is what is typed


def prompt_weak_key_load(prompt: str, language: str, weak_keys: set[str]) -> int:
    romaji = _to_romaji(prompt, language)
    return sum(1 for ch in romaji if ch in weak_keys)


def select_adaptive(
    prompts: list[str],
    language: str,
    stats: KeyStats,
    count: int,
    seed: int | None = None,
) -> list[str]:
    if not prompts:
        return []
    weak = set(stats.weakest(8))
    weights = [1.0 + prompt_weak_key_load(p, language, weak) for p in prompts]
    rng = random.Random(seed)
    # weighted sampling without immediate repeats where possible
    picks: list[str] = []
    pool = list(prompts)
    pool_w = list(weights)
    for _ in range(count):
        chosen = rng.choices(pool, weights=pool_w, k=1)[0]
        picks.append(chosen)
    return picks
