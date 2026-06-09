from __future__ import annotations

import argparse
import sys
import time

from split_typing.engine import Score, score_attempt
from split_typing.llm import generate_prompts
from split_typing.prompts import available_languages, get_prompts, levels_for_language


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Split keyboard typing trainer")
    parser.add_argument("--language", choices=available_languages(), help="practice track")
    parser.add_argument("--level", type=int, choices=(1, 2, 3, 4), help="difficulty level")
    parser.add_argument("--count", type=int, default=5, help="number of prompts")
    parser.add_argument("--seed", type=int, help="deterministic fixed prompt selection")
    parser.add_argument("--llm", action="store_true", help="try generating prompts with Ollama")
    parser.add_argument("--model", default="gemma4:26b", help="Ollama model name")
    parser.add_argument("--list", action="store_true", help="list tracks and levels")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list:
        print_catalog()
        return 0

    language = args.language or choose_language()
    level = args.level or choose_level(language)
    count = max(args.count, 1)

    prompts = []
    if args.llm:
        print(f"Generating prompts with Ollama model {args.model}...")
        prompts = generate_prompts(language, level, count, args.model)
        if not prompts:
            print("LLM generation failed or returned no prompts. Falling back to fixed drills.")

    if not prompts:
        prompts = get_prompts(language, level, count, args.seed)

    scores = run_session(language, level, prompts)
    print_summary(scores)
    return 0


def print_catalog() -> None:
    print("Tracks:")
    for language in available_languages():
        levels = ", ".join(str(level) for level in levels_for_language(language))
        print(f"  {language}: levels {levels}")


def choose_language() -> str:
    languages = available_languages()
    while True:
        print_catalog()
        choice = input("language> ").strip().lower()
        if choice in languages:
            return choice
        print("Choose one of: " + ", ".join(languages))


def choose_level(language: str) -> int:
    levels = levels_for_language(language)
    while True:
        choice = input(f"level {levels}> ").strip()
        if choice.isdigit() and int(choice) in levels:
            return int(choice)
        print("Choose level 1, 2, 3, or 4.")


def run_session(language: str, level: int, prompts: list[str]) -> list[Score]:
    print(f"\nTrack: {language}  Level: {level}  Prompts: {len(prompts)}")
    print("Type each prompt and press Enter. Type q alone to stop.\n")
    scores: list[Score] = []

    for index, prompt in enumerate(prompts, start=1):
        print(f"[{index}/{len(prompts)}] {prompt}")
        started = time.perf_counter()
        try:
            actual = input("> ")
        except EOFError:
            print()
            break
        elapsed = time.perf_counter() - started
        if actual == "q":
            break

        score = score_attempt(prompt, actual, elapsed)
        scores.append(score)
        print_feedback(score)
        print()
    return scores


def print_feedback(score: Score) -> None:
    accuracy = score.accuracy * 100
    print(f"accuracy {accuracy:.1f}% | errors {score.errors} | {score.wpm:.1f} WPM | {score.cpm:.1f} CPM")
    if score.mismatches:
        parts = [f"{pos}:{want or '∅'}->{got or '∅'}" for pos, want, got in score.mismatches[:5]]
        print("mismatch " + ", ".join(parts))


def print_summary(scores: list[Score]) -> None:
    if not scores:
        print("No completed prompts.")
        return
    avg_accuracy = sum(score.accuracy for score in scores) / len(scores) * 100
    avg_wpm = sum(score.wpm for score in scores) / len(scores)
    total_errors = sum(score.errors for score in scores)
    print("Session summary")
    print(f"  completed: {len(scores)}")
    print(f"  average accuracy: {avg_accuracy:.1f}%")
    print(f"  average WPM: {avg_wpm:.1f}")
    print(f"  total errors: {total_errors}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
