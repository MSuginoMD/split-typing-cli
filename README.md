# Split Typing CLI

Local typing trainer for getting used to a split keyboard.

## Run

```bash
cd /Users/msugino/Projects/split-typing-cli
python3 typing_game.py
```

List tracks:

```bash
python3 typing_game.py --list
```

Run a fixed drill:

```bash
python3 typing_game.py --language english --level 1 --count 5
python3 typing_game.py --language japanese --level 3 --count 5
python3 typing_game.py --language python --level 4 --count 3
```

Use local Gemma through Ollama when available:

```bash
python3 typing_game.py --language english --level 2 --count 5 --llm --model gemma4
```

If Ollama or the model fails, the app falls back to fixed drills.

## Levels

- `1`: short words and basic key clusters
- `2`: short phrases and common tokens
- `3`: full sentences or code-like lines
- `4`: longer text or small Python snippets

## Tests

```bash
python3 -m unittest discover -s tests -v
```
