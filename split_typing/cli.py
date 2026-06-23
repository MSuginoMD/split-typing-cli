from __future__ import annotations

import argparse
import sys
import time

from split_typing.adaptive import select_adaptive
from split_typing.engine import RealtimeSession, Score, score_attempt
from split_typing.input_capture import read_keys, supports_raw
from split_typing.llm import generate_prompts
from split_typing.prompts import available_languages, get_prompts, levels_for_language
from split_typing.reading import pykakasi_available, to_hiragana
from split_typing.stats import KeyStats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Split keyboard typing trainer")
    parser.add_argument("--language", choices=available_languages(), help="practice track")
    parser.add_argument("--level", type=int, choices=(1, 2, 3, 4), help="difficulty level")
    parser.add_argument("--count", type=int, default=None, help="number of prompts (default 5)")
    parser.add_argument("--seed", type=int, help="deterministic fixed prompt selection")
    parser.add_argument("--llm", action="store_true", help="try generating prompts with Ollama")
    parser.add_argument("--model", default="gemma4:26b", help="Ollama model name")
    parser.add_argument("--list", action="store_true", help="list tracks and levels")
    parser.add_argument("--classic", action="store_true", help="line-input mode")
    parser.add_argument("--adaptive", action="store_true", help="bias prompts to weak keys")
    parser.add_argument("--stats", action="store_true", help="show weak keys and exit")
    parser.add_argument("--no-color", action="store_true", help="disable ANSI color")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list:
        print_catalog()
        return 0

    if args.stats:
        stats = KeyStats.load()
        print_weak_keys(stats)
        return 0

    # Interactive launch: when the track wasn't given on the command line we
    # prompt for everything (language, level, and whether to use the LLM) so the
    # tool is usable as a menu, not just via flags.
    interactive = args.language is None and sys.stdin.isatty()

    language = args.language or choose_language()
    level = args.level or choose_level(language)
    if args.count is not None:
        count = max(args.count, 1)
    elif interactive:
        count = choose_count()
    else:
        count = 5

    use_adaptive = args.adaptive
    if interactive and not use_adaptive:
        use_adaptive = choose_yes_no("Focus on your weak keys (adaptive)?", default=False)

    use_llm = args.llm
    if interactive and not use_llm:
        use_llm = choose_yes_no(
            "Generate fresh prompts with a local Ollama model (slower)?", default=False
        )

    prompts = []
    if use_llm:
        print(f"Generating prompts with Ollama model {args.model}...")
        prompts = generate_prompts(language, level, count, args.model)
        if not prompts:
            print("LLM generation failed or returned no prompts. Falling back to fixed drills.")

    if not prompts:
        prompts = get_prompts(language, level, count, args.seed)

    use_realtime = not args.classic and supports_raw()

    if use_realtime and language == "japanese" and not pykakasi_available():
        print(
            "Warning: pykakasi is not installed; kanji cannot be converted to hiragana.\n"
            "Falling back to classic (line-input) mode."
        )
        use_realtime = False

    if use_realtime:
        stats = KeyStats.load()
        if use_adaptive:
            prompts = select_adaptive(prompts, language, stats, count, args.seed)

        color = not args.no_color
        pairs = [
            (p, to_hiragana(p) if language == "japanese" else p)
            for p in prompts
        ]
        print(f"\nTrack: {language}  Level: {level}  Prompts: {len(pairs)}")
        print("Type each prompt. ESC/Tab to skip, Ctrl-C to quit.\n")
        completed = 0
        session_errors = 0
        try:
            for index, (display, reading_kana) in enumerate(pairs, start=1):
                print(f"[{index}/{len(pairs)}] ", end="")
                sess = run_realtime_prompt(display, reading_kana, stats, color)
                if sess.done:
                    completed += 1
                session_errors += sess.errors
        except KeyboardInterrupt:
            print()
        finally:
            stats.save()
        print_realtime_summary(completed, len(pairs), session_errors, stats)
        return 0

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
    print("Choose a language:")
    for i, lang in enumerate(languages, start=1):
        print(f"  {i}. {lang}")
    while True:
        choice = input("language (number or name)> ").strip().lower()
        if choice.isdigit() and 1 <= int(choice) <= len(languages):
            return languages[int(choice) - 1]
        if choice in languages:
            return choice
        print("Enter a number 1-%d or one of: %s" % (len(languages), ", ".join(languages)))


def choose_level(language: str) -> int:
    levels = levels_for_language(language)
    hints = {1: "short words", 2: "short phrases", 3: "sentences", 4: "longer text"}
    print(f"Choose a level for {language}:")
    for lvl in levels:
        print(f"  {lvl}. {hints.get(lvl, '')}".rstrip())
    while True:
        choice = input("level> ").strip()
        if choice.isdigit() and int(choice) in levels:
            return int(choice)
        print("Choose one of: " + ", ".join(str(lvl) for lvl in levels))


def choose_count(default: int = 5) -> int:
    while True:
        choice = input(f"how many prompts? [default {default}]> ").strip()
        if not choice:
            return default
        if choice.isdigit() and int(choice) >= 1:
            return int(choice)
        print("Enter a positive number (or press Enter for %d)." % default)


def choose_yes_no(question: str, default: bool = False) -> bool:
    suffix = " [y/N]> " if not default else " [Y/n]> "
    while True:
        choice = input(question + suffix).strip().lower()
        if not choice:
            return default
        if choice in ("y", "yes"):
            return True
        if choice in ("n", "no"):
            return False
        print("Please answer y or n.")


def print_weak_keys(stats: KeyStats) -> None:
    weak = stats.weakest(10)
    if not weak:
        print("No stats yet. Do a realtime session first.")
        return
    print("Weakest keys (worst first):")
    for k in weak:
        e = stats.data[k]
        rate = e["errors"] / e["count"] * 100
        print(f"  {k!r}: {rate:.0f}% errors, {e['ema_ms']:.0f}ms avg, n={e['count']}")


def _render(sess: RealtimeSession, color: bool) -> None:
    typed = sess.typed
    if color:
        line = f"\r\x1b[2K{typed}\x1b[90m{sess.hint}\x1b[0m"
    else:
        line = f"\r\x1b[2K{typed}|{sess.hint}"
    print(line, end="", flush=True)


def run_realtime_prompt(display: str, reading: str, stats: KeyStats, color: bool) -> RealtimeSession:
    sess = RealtimeSession(reading, stats=stats)
    print(display)
    last = time.perf_counter()
    keys = read_keys()
    for ch in keys:
        if ch in ("\x1b", "\t"):   # ESC / Tab -> skip prompt
            print("  [skipped]")
            return sess
        now = time.perf_counter()
        ms = (now - last) * 1000.0
        last = now
        if ch in ("\x7f", "\b"):
            sess.backspace()
        else:
            sess.key(ch, ms)
        _render(sess, color)
        if sess.done:
            print()
            return sess
    return sess


def print_realtime_summary(completed: int, total: int, errors: int, stats: KeyStats) -> None:
    print("\nSession summary")
    print(f"  completed: {completed}/{total}")
    print(f"  errors this session: {errors}")
    print()
    print_weak_keys(stats)
    print("\nTip: run with --adaptive (or pick it at launch) to drill your weak keys.")


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
