# Split Typing CLI Design

## Goal

Build a local command-line typing trainer for adapting to the roBa split keyboard. It should start with short words and progress to longer sentences, with separate practice tracks for Japanese, English, and Python.

## Approach

The app is a dependency-free Python CLI. It ships with fixed drills so it works offline, and adds an optional LLM generation mode through `ollama run gemma4` when requested. If Ollama or the model is unavailable, the CLI falls back to the fixed drills and reports the fallback clearly.

## Components

- `split_typing.prompts`: fixed prompt bank and selection logic by language and level.
- `split_typing.engine`: timing, accuracy, WPM/CPM, and mismatch calculation.
- `split_typing.llm`: small Ollama wrapper that asks for plain prompt lines only.
- `split_typing.cli`: argparse interface and interactive game loop.
- `typing_game.py`: launcher for convenient local execution.

## User Flow

The user runs `python3 typing_game.py`, chooses language and level, then types each displayed prompt followed by Enter. The app prints per-prompt feedback and a session summary. Flags can skip menus, for example `--language python --level 3 --count 8 --llm`.

## Practice Content

Levels are consistent across languages:

1. Short words and key clusters.
2. Phrases and common programming tokens.
3. Full sentences or code-like lines.
4. Longer paragraphs or small Python snippets.

English drills include split-keyboard adaptation material based on the recovered roBa layer 0 letters and common modifier/symbol stretches. Japanese drills use kana/romaji-friendly short phrases and sentences. Python drills focus on symbols, indentation, identifiers, and common statements.

## Error Handling

Invalid language or level falls back to interactive choices. Empty answers are scored as zero accuracy. Ollama failures return fixed prompts without crashing.

## Testing

Use `unittest` only. Tests cover prompt selection, scoring accuracy, mismatch reporting, and LLM fallback parsing.
