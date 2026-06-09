# Split Typing CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dependency-free local Python typing trainer with Japanese, English, Python, and optional Gemma/Ollama generated drills.

**Architecture:** Keep the project as a small Python package with focused modules for prompts, scoring, LLM generation, and CLI orchestration. The CLI depends on stable module APIs and can fall back to fixed prompts whenever LLM generation fails.

**Tech Stack:** Python 3.14 standard library, `unittest`, optional local `ollama` executable.

---

### Task 1: Prompt Bank And Selection

**Files:**
- Create: `split_typing/prompts.py`
- Create: `tests/test_prompts.py`

- [ ] Write tests for language listing, level selection, and invalid language handling.
- [ ] Implement fixed prompt bank for `english`, `japanese`, and `python`.
- [ ] Run `python3 -m unittest tests.test_prompts -v`.

### Task 2: Scoring Engine

**Files:**
- Create: `split_typing/engine.py`
- Create: `tests/test_engine.py`

- [ ] Write tests for exact match, typo mismatch, empty input, and speed metrics.
- [ ] Implement `score_attempt(expected, actual, seconds)`.
- [ ] Run `python3 -m unittest tests.test_engine -v`.

### Task 3: Optional Ollama Integration

**Files:**
- Create: `split_typing/llm.py`
- Create: `tests/test_llm.py`

- [ ] Write tests for parsing generated lines and subprocess fallback.
- [ ] Implement `generate_prompts(language, level, count, model)`.
- [ ] Run `python3 -m unittest tests.test_llm -v`.

### Task 4: CLI Game Loop

**Files:**
- Create: `split_typing/cli.py`
- Create: `split_typing/__init__.py`
- Create: `typing_game.py`

- [ ] Implement argparse flags: `--language`, `--level`, `--count`, `--llm`, `--model`, `--seed`, `--list`.
- [ ] Implement interactive selection and line-by-line typing loop.
- [ ] Run `python3 typing_game.py --list`.
- [ ] Run `printf 'q\\n' | python3 typing_game.py --language english --level 1 --count 1`.

### Task 5: Documentation And Full Verification

**Files:**
- Create: `README.md`

- [ ] Document common commands and Ollama mode.
- [ ] Run `python3 -m unittest -v`.
- [ ] Run smoke tests for fixed and fallback LLM modes.
