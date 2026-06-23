# Split Typing CLI

A real-time, adaptive CLI typing trainer designed for split keyboards, with first-class Japanese support. Type characters one keystroke at a time and get instant per-key feedback — correct keystrokes light up green, errors flash red, and a ghost hint shows what's still left to type. Weak-key stats persist between sessions so the trainer can automatically bias future drills toward the letters you struggle with most (keybr-style adaptive mode). Japanese practice displays natural kanji sentences while you type the romaji of the reading, with flexible multi-variant acceptance (shi/si, n/nn, and more). Requires Python ≥ 3.10, macOS or Linux.

---

## Features

- **Realtime per-keystroke feedback** — live coloring (green/red/grey) as you type each character; no waiting for Enter.
- **Adaptive drills** — tracks per-key error rate and latency in `~/.split-typing/stats.json`; `--adaptive` biases prompt selection toward your weakest keys.
- **Japanese kanji → romaji practice** — display a natural kanji sentence, type the romaji of its reading. Multi-variant acceptance: `shi`/`si`, `chi`/`ti`, `tsu`/`tu`, word-final `ん` as `n` or `nn`, ASCII `,`/`.` for `、`/`。`. Reading conversion is done by **pykakasi** (pure Python, no external tools needed).
- **Classic line-input fallback** — `--classic` uses the original `input()`-based flow; useful when your IME is on, when piping input, or on non-TTY environments. Realtime mode auto-falls back to classic when stdin/stdout is not a TTY.
- **Optional local LLM generation** — `--llm` calls a local [Ollama](https://ollama.com) server to generate varied prompts; falls back to the static bank if the model is unavailable.
- **English and Python tracks** — standard words/phrases/code snippets at four difficulty levels.
- **`--stats`** — print your weakest keys and exit (no drill).

---

## Install

Requires Python ≥ 3.10. A virtual environment is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

This installs the `split-typing` command and the `pykakasi` dependency automatically.

---

## Usage

### Interactive (no flags)

```bash
split-typing
```

Prompts for language and level interactively.

### Specify track, level, and count

```bash
split-typing --language english --level 2 --count 10
split-typing --language japanese --level 3 --count 5
split-typing --language python --level 4 --count 3
```

`--level` accepts 1–4 (1 = short/easy, 4 = longer/harder).

### Adaptive mode

```bash
split-typing --adaptive
```

Biases prompt selection toward your historically weak keys.

### Show your stats

```bash
split-typing --stats
```

Prints the keys with the highest error rates and slowest latency, then exits.

### Classic line-input mode

```bash
split-typing --classic
```

Uses the original Enter-to-submit flow. Good for Japanese with IME enabled or when running in a non-TTY environment.

### Optional Ollama LLM generation

```bash
split-typing --llm --model gemma2
```

Generates prompts via a local Ollama model. The built-in default model name may not be installed on your machine — pass `--model <name>` to match a model you have (e.g. `gemma2`, `llama3`). Falls back to the static bank on failure.

### List tracks and levels

```bash
split-typing --list
```

### Other flags

| Flag | Effect |
|------|--------|
| `--count N` | Number of prompts per session (default 5) |
| `--seed N` | Deterministic prompt selection |
| `--no-color` | Disable ANSI colors |

---

## How Japanese Works

1. **IME must be OFF.** You type raw romaji.
2. The trainer displays a natural Japanese sentence (kanji/kana).
3. Internally, **pykakasi** converts it to a hiragana reading, which becomes the target.
4. You type the romaji of that reading, one character at a time.
5. Multiple romaji spellings are accepted for the same kana — for example `し` accepts both `shi` and `si`; word-final `ん` accepts both `n` and `nn`.
6. Press **Tab** or **ESC** to skip a prompt (e.g. if pykakasi mis-read an unusual word). Skipped prompts are excluded from key stats.

Note: pykakasi can occasionally mis-read context-dependent words (e.g. `今日` read as `こんにち` instead of `きょう`). The skip key is there for exactly this case.

---

## Notes

- **POSIX only** — realtime raw mode uses `termios`/`tty` (macOS and Linux). Classic mode works everywhere.
- **Stats file** — per-key stats are stored at `~/.split-typing/stats.json` (outside the repo).
- **Auto-fallback** — if stdout is not a TTY (e.g. piped), the session automatically uses classic mode.

---

## Running Tests

```bash
python -m unittest discover -s tests
```

A virtual environment with `pykakasi` installed is required:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m unittest discover -s tests
```

---

## License

MIT
