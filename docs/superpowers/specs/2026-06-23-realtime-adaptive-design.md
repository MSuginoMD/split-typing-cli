# Split Typing CLI — Realtime & Adaptive Evolution (Design Spec)

Date: 2026-06-23
Status: Approved (design), pending spec review

## Purpose

Evolve the existing `split-typing-cli` line-input typing trainer into a
**real-time, per-keystroke** trainer that measures which keys are slow or
error-prone and **adapts future drills to the user's weak keys** (keybr-style).
Primary user goal: get faster on a split keyboard (roBa / Keyball-style),
practicing discreetly in a terminal (no browser). Japanese is the main use case.

Final deliverable: the project, cleaned up and **published as a public GitHub
repository**.

## Background / Findings

- The existing app uses line-based `input()` (type a whole line, press Enter).
  It cannot measure per-key latency or which keys are weak.
- The static Japanese prompt bank is tiny and reads as "childish" — this, not
  the LLM, was the cause of the "poor vocabulary" complaint. The user was
  running without `--llm`, so only the small static bank appeared.
- `gemma4:26b` and `gemma4:latest` ARE installed and produce **natural, varied**
  Japanese (verified). The LLM is good; we just need to actually use it and
  enrich the static fallback.
- For "kana display → type romaji", kanji cannot be deterministically converted
  to romaji. Decision: **display the natural sentence (kanji incl.), convert the
  reading internally with pykakasi**, and accept the romaji of that reading.
- `pykakasi` (pure Python) installs and runs on **Python 3.14** (verified in a
  throwaway venv) and gives accurate readings for common sentences. It DOES
  mis-read context-dependent forms (e.g. `今日は市場` → `こんにちは しじょう`),
  so fairness mitigation is required.
- Particles: pykakasi hepburn gives は→`ha`, を→`wo`, へ→`he`, which is exactly
  what one types with an IME — correct for our purposes.

## Approved Approach: A — layered additions to the existing package

Keep the working modules (`engine.py` scoring, `prompts.py` bank, `llm.py`
ollama). Add focused, independently testable modules. Keep the old line-input
flow as `--classic` for IME-on Japanese and non-TTY environments.

## Architecture

| Module | Responsibility | Testing |
|---|---|---|
| `input_capture.py` | Raw-mode keystroke reader (termios/tty, POSIX). Yields `(char, timestamp)` events. Handles backspace, Ctrl-C, ESC/Tab to skip. Thin TTY-only layer. | Smoke/manual; logic kept out of it |
| `romaji.py` ⭐ | kana→romaji flexible matcher (state machine). Pure functions. The heart. | Heavy unit tests |
| `reading.py` | pykakasi wrapper: natural sentence → hiragana reading. Isolated; degrades gracefully if pykakasi missing. | Golden/integration tests |
| `stats.py` | Persistent per-key stats store (`~/.split-typing/stats.json`). Load/save + pure update/scoring logic. | Unit tests |
| `adaptive.py` | Weak-key scoring + weighted prompt selection/generation. Pure. | Seeded deterministic tests |
| `engine.py` | Add real-time match loop driven by keystroke events. Keep `score_attempt` for classic mode. | Unit tests on the loop logic |
| `cli.py` | Wire modes: realtime (default) + `--classic`; live colored rendering; new flags. | Smoke |
| `prompts.py` | Keep + enrich static bank (fallback). | Existing tests |
| `llm.py` | Keep; ensure Japanese generation yields natural sentences; make LLM easier to use. | Existing tests |

## Data Flow (Japanese, realtime)

1. Get prompt: gemma natural sentence OR static/adaptive bank.
2. `reading.py`: sentence → hiragana reading (pykakasi).
3. `romaji.py`: reading → DAG of acceptable romaji per kana unit.
4. Display: the natural (kanji) sentence + live romaji underneath, colored per
   char (correct / wrong / pending).
5. Each keystroke → `matcher.advance(char)` → correct/incorrect + timestamp.
6. On completion: per-key timings/errors → `stats.py`.
7. `adaptive.py` uses accumulated stats to bias the next prompts toward weak keys.

English / Python skip steps 2–3 (the "reading" is the literal text; the matcher
is identity-with-timing).

## Romaji State Machine (the heart) — `romaji.py`

- Tokenize the hiragana reading into **kana units**: base kana, youon (きゃ),
  sokuon っ, ん, long vowel ー, punctuation/space passthrough.
- Each unit → set of acceptable romaji strings (table-driven). Examples:
  し→{shi,si}, つ→{tsu,tu}, ち→{chi,ti}, じ→{ji,zi}, ふ→{fu,hu}, を→{wo,o},
  は(particle)→{ha}, づ→{du,zu}, ー→{`-`, repeat-of-previous-vowel}.
- そくおん っ: prepend the doubled leading consonant to each variant of the
  next unit.
- ん: {n, nn, n'}. Accept bare `n` only when the next unit does not start with a
  vowel / n / y; otherwise require `nn` (classic IME rule).
- Live matcher: keep current unit index + a buffer for the current unit. On each
  char, append and check the buffer is a prefix of some variant; on an exact
  variant match (with the `n` lookahead rule), advance to the next unit.
- Backspace rewinds within/across units.
- Pure and heavily unit-tested (variants, sokuon, ん disambiguation, youon, long
  vowel, punctuation, spaces).

## Fairness Mitigation for pykakasi Misreads

- After N consecutive wrong chars at a position, reveal the expected kana reading
  inline as a hint.
- A **skip key** (Tab or ESC) abandons the current prompt so a bad reading never
  traps the user; skipped prompts are excluded from key stats.
- Multi-variant acceptance (は/を/へ, shi/si, etc.) absorbs most differences.
- (Out of scope v1) a user correction dictionary for persistent misreads.

## Stats & Adaptive

- `~/.split-typing/stats.json`: per key (latin char) → `{count, errors,
  total_time_ms, ema_latency_ms}`.
- Weakness score = weighted combination of error rate and latency (normalized).
- Adaptive selection: weight available prompts by weak-key content; plus a
  focus-drill generator emphasizing the top-N weak keys (Japanese: reverse-index
  kana whose romaji contains the weak latin keys).
- v1 keeps adaptive simple (weighted selection + focus drills). LLM-based
  weak-key enrichment is optional, not required.

## CLI / Modes / Errors

- Default: realtime mode.
- `--classic`: old line-input mode (IME-on Japanese, non-TTY).
- Retained: `--language --level --count --seed --llm --model --list`.
- New: `--adaptive` (use stats to pick), `--stats` (show weak keys / progress),
  `--no-color`.
- Auto-fallback to classic when stdin/stdout is not a TTY or termios is
  unavailable.
- Raw mode always restored via try/finally (including on Ctrl-C).
- pykakasi import failure → Japanese realtime degrades (message + classic or
  romaji-direct). ollama failure → static/adaptive bank (existing behavior).

## Testing

- `romaji.py`: extensive unit tests (the critical surface).
- `stats.py`, `adaptive.py`: pure, seeded deterministic tests.
- `reading.py`: a few golden tests guarding against pykakasi regressions
  (integration-tagged; depends on the library).
- `engine.py` realtime loop: unit tests feeding synthetic keystroke events.
- `input_capture.py` / `cli.py` realtime: thin; smoke/manual only.

## Dependencies

- Add **pykakasi** (pure Python, verified on 3.14). English/Python path keeps
  zero hard runtime deps.
- Declare deps in `pyproject.toml` (and/or `requirements.txt`).

## Public Release Requirements

- Rewrite `README.md` for a general audience: no personal absolute paths
  (`/Users/msugino/...`), generic install/run instructions, feature overview,
  examples, optional asciinema/GIF.
- Add `LICENSE` (MIT, unless the user prefers otherwise).
- `pyproject.toml` with metadata, console entry point (`split-typing`), and
  pykakasi dependency.
- Verify `.gitignore` excludes venvs, caches, and any local data
  (`~/.split-typing/` is outside the repo by design).
- Scrub repo for secrets / personal info before publishing.
- Decide whether to keep `docs/superpowers/` planning docs (harmless to keep;
  may be moved to a `docs/` subfolder).
- Create a **public GitHub repo** and push. Repo name, license choice, GitHub
  account, and public/private to be confirmed with the user immediately before
  pushing.

## YAGNI / Out of Scope (v1)

- No fancy graphs (simple text stats only); minimal/optional streak.
- No multi-user, no cloud sync, no GUI.
- No Windows raw-mode support in v1 (POSIX termios; classic mode still works).
- No correction dictionary for pykakasi misreads.
```