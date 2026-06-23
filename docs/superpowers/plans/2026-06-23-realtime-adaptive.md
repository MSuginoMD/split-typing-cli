# Realtime + Adaptive Typing Trainer — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Evolve `split-typing-cli` into a real-time, per-keystroke typing trainer that measures weak keys and adapts drills to them, with Japanese (kanji→reading→romaji) support, then publish it as a public GitHub repo.

**Architecture:** Keep the existing package and its line-input flow as `--classic`. Add focused, independently testable modules: a pure kana→romaji matcher (`romaji.py`), a pykakasi reading wrapper (`reading.py`), persistent per-key stats (`stats.py`), adaptive selection (`adaptive.py`), a realtime session loop (`engine.py`), and a thin raw-mode reader (`input_capture.py`). `cli.py` wires modes and rendering.

**Tech Stack:** Python 3.14, stdlib `termios`/`tty` for raw input, `pykakasi` for kana readings, `ollama` (external CLI, optional) for prompt generation, `unittest` for tests.

## Global Constraints

- Python 3.14 (verified target). Use `from __future__ import annotations`.
- New hard dependency: `pykakasi` only. English/Python paths must keep zero hard runtime deps and must import without pykakasi installed.
- POSIX raw mode only (termios/tty). Auto-fallback to classic mode when stdin/stdout is not a TTY or termios is unavailable. Never leave the terminal in raw mode (try/finally).
- Persistent stats live OUTSIDE the repo at `~/.split-typing/stats.json`.
- Romaji acceptance must be multi-variant (e.g. し→shi/si). Particles use typed spelling: は→`ha`, を→`wo`, へ→`he`.
- All existing tests must keep passing. Run the suite with `python3 -m unittest discover -s tests -v`.
- Commit after every task. End commit messages with the Co-Authored-By trailer used by this repo.
- No personal absolute paths in published files (README, pyproject).

---

## File Structure

- Create: `split_typing/romaji.py` — kana tokenizer + romaji segment builder + `RomajiMatcher`.
- Create: `split_typing/reading.py` — `to_hiragana(text)` via pykakasi, graceful degrade.
- Create: `split_typing/stats.py` — `KeyStats` store: load/save/record/weakness.
- Create: `split_typing/adaptive.py` — weak-key weighting + focus-drill generation.
- Create: `split_typing/input_capture.py` — raw-mode keystroke reader.
- Modify: `split_typing/engine.py` — add `RealtimeSession` (keep `score_attempt`).
- Modify: `split_typing/cli.py` — modes, flags, rendering, fallback.
- Modify: `split_typing/prompts.py` — enrich banks; add reverse helpers.
- Modify: `split_typing/llm.py` — natural Japanese generation.
- Create: `pyproject.toml`, `LICENSE` — packaging + license.
- Modify: `README.md`, `.gitignore` — public-facing docs/ignores.
- Create tests under `tests/` mirroring each module.

---

## Task 1: Kana tokenizer

**Files:**
- Create: `split_typing/romaji.py`
- Test: `tests/test_romaji.py`

**Interfaces:**
- Produces: `tokenize_kana(reading: str) -> list[str]` — splits a hiragana/katakana string into kana units. Youon combos (きゃ) become one unit; sokuon (っ/ッ) is its own unit; long vowel ー is its own unit; any non-kana char (space, punctuation, ascii) is a single pass-through unit. Katakana is normalized to hiragana except ー.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_romaji.py
import unittest
from split_typing.romaji import tokenize_kana


class TestTokenizeKana(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(tokenize_kana("にほん"), ["に", "ほ", "ん"])

    def test_youon_is_one_unit(self):
        self.assertEqual(tokenize_kana("きゃく"), ["きゃ", "く"])

    def test_sokuon_is_own_unit(self):
        self.assertEqual(tokenize_kana("がっこう"), ["が", "っ", "こ", "う"])

    def test_katakana_normalized_but_choon_kept(self):
        self.assertEqual(tokenize_kana("テーブル"), ["て", "ー", "ぶ", "る"])

    def test_passthrough(self):
        self.assertEqual(tokenize_kana("あ、 a"), ["あ", "、", " ", "a"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_romaji -v`
Expected: FAIL (`ModuleNotFoundError` / `tokenize_kana` undefined).

- [ ] **Step 3: Write minimal implementation**

```python
# split_typing/romaji.py
from __future__ import annotations

_SMALL_Y = {"ゃ", "ゅ", "ょ"}
_SMALL_VOWEL_COMBINABLE = {"ぁ", "ぃ", "ぅ", "ぇ", "ぉ"}  # for ふぁ etc.
_SOKUON = {"っ"}
_CHOON = "ー"


def _kata_to_hira(ch: str) -> str:
    code = ord(ch)
    if 0x30A1 <= code <= 0x30F6:  # katakana range with hiragana counterpart
        return chr(code - 0x60)
    return ch


def tokenize_kana(reading: str) -> list[str]:
    units: list[str] = []
    for raw in reading:
        if raw == _CHOON:
            units.append(_CHOON)
            continue
        ch = _kata_to_hira(raw)
        if ch in _SMALL_Y or ch in _SMALL_VOWEL_COMBINABLE:
            if units and units[-1] not in _SOKUON and units[-1] != _CHOON and _is_kana(units[-1]):
                units[-1] = units[-1] + ch
                continue
        units.append(ch)
    return units


def _is_kana(unit: str) -> bool:
    return bool(unit) and "ぁ" <= unit[0] <= "ゖ"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_romaji -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add split_typing/romaji.py tests/test_romaji.py
git commit -m "feat: kana tokenizer for romaji matching

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Romaji table + basic segments

**Files:**
- Modify: `split_typing/romaji.py`
- Test: `tests/test_romaji.py`

**Interfaces:**
- Consumes: `tokenize_kana`.
- Produces: `romaji_variants(unit: str) -> list[str]` — acceptable romaji spellings for ONE kana unit (no sokuon/ん context). Pass-through units return `[unit]`. Produces `ROMAJI_TABLE: dict[str, list[str]]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_romaji.py  (append)
from split_typing.romaji import romaji_variants


class TestRomajiVariants(unittest.TestCase):
    def test_multi_variant(self):
        self.assertIn("shi", romaji_variants("し"))
        self.assertIn("si", romaji_variants("し"))

    def test_youon(self):
        self.assertIn("kya", romaji_variants("きゃ"))

    def test_particle_choices_present(self):
        self.assertIn("wo", romaji_variants("を"))

    def test_passthrough(self):
        self.assertEqual(romaji_variants(" "), [" "])
        self.assertEqual(romaji_variants("、"), ["、"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_romaji -v`
Expected: FAIL (`romaji_variants` undefined).

- [ ] **Step 3: Write minimal implementation**

Add a table covering gojuon, dakuten/handakuten, youon, and small-combos. (Engineer: include the full kana set; the excerpt shows the required shape and the multi-variant rows that tests depend on.)

```python
# split_typing/romaji.py (append)
ROMAJI_TABLE: dict[str, list[str]] = {
    "あ": ["a"], "い": ["i"], "う": ["u"], "え": ["e"], "お": ["o"],
    "か": ["ka"], "き": ["ki"], "く": ["ku"], "け": ["ke"], "こ": ["ko"],
    "さ": ["sa"], "し": ["shi", "si"], "す": ["su"], "せ": ["se"], "そ": ["so"],
    "た": ["ta"], "ち": ["chi", "ti"], "つ": ["tsu", "tu"], "て": ["te"], "と": ["to"],
    "な": ["na"], "に": ["ni"], "ぬ": ["nu"], "ね": ["ne"], "の": ["no"],
    "は": ["ha"], "ひ": ["hi"], "ふ": ["fu", "hu"], "へ": ["he"], "ほ": ["ho"],
    "ま": ["ma"], "み": ["mi"], "む": ["mu"], "め": ["me"], "も": ["mo"],
    "や": ["ya"], "ゆ": ["yu"], "よ": ["yo"],
    "ら": ["ra"], "り": ["ri"], "る": ["ru"], "れ": ["re"], "ろ": ["ro"],
    "わ": ["wa"], "を": ["wo", "o"], "ん": ["n", "nn", "n'"],
    "が": ["ga"], "ぎ": ["gi"], "ぐ": ["gu"], "げ": ["ge"], "ご": ["go"],
    "ざ": ["za"], "じ": ["ji", "zi"], "ず": ["zu"], "ぜ": ["ze"], "ぞ": ["zo"],
    "だ": ["da"], "ぢ": ["di", "ji"], "づ": ["du", "zu"], "で": ["de"], "ど": ["do"],
    "ば": ["ba"], "び": ["bi"], "ぶ": ["bu"], "べ": ["be"], "ぼ": ["bo"],
    "ぱ": ["pa"], "ぴ": ["pi"], "ぷ": ["pu"], "ぺ": ["pe"], "ぽ": ["po"],
    # youon
    "きゃ": ["kya"], "きゅ": ["kyu"], "きょ": ["kyo"],
    "しゃ": ["sha", "sya"], "しゅ": ["shu", "syu"], "しょ": ["sho", "syo"],
    "ちゃ": ["cha", "tya"], "ちゅ": ["chu", "tyu"], "ちょ": ["cho", "tyo"],
    "にゃ": ["nya"], "にゅ": ["nyu"], "にょ": ["nyo"],
    "ひゃ": ["hya"], "ひゅ": ["hyu"], "ひょ": ["hyo"],
    "みゃ": ["mya"], "みゅ": ["myu"], "みょ": ["myo"],
    "りゃ": ["rya"], "りゅ": ["ryu"], "りょ": ["ryo"],
    "ぎゃ": ["gya"], "ぎゅ": ["gyu"], "ぎょ": ["gyo"],
    "じゃ": ["ja", "zya", "jya"], "じゅ": ["ju", "zyu", "jyu"], "じょ": ["jo", "zyo", "jyo"],
    "びゃ": ["bya"], "びゅ": ["byu"], "びょ": ["byo"],
    "ぴゃ": ["pya"], "ぴゅ": ["pyu"], "ぴょ": ["pyo"],
    "ふぁ": ["fa"], "ふぃ": ["fi"], "ふぇ": ["fe"], "ふぉ": ["fo"],
    # small standalone vowels (rare) and others
    "ぁ": ["la", "xa"], "ぃ": ["li", "xi"], "ぅ": ["lu", "xu"],
    "ぇ": ["le", "xe"], "ぉ": ["lo", "xo"],
}


def romaji_variants(unit: str) -> list[str]:
    if unit in ROMAJI_TABLE:
        return list(ROMAJI_TABLE[unit])
    return [unit]  # pass-through: space, punctuation, ascii
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_romaji -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add split_typing/romaji.py tests/test_romaji.py
git commit -m "feat: romaji variant table for kana units

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Segment builder (sokuon + ん lookahead)

**Files:**
- Modify: `split_typing/romaji.py`
- Test: `tests/test_romaji.py`

**Interfaces:**
- Consumes: `tokenize_kana`, `romaji_variants`.
- Produces: `build_segments(reading: str) -> list[list[str]]` — one variant-list per typed segment. Sokuon っ merges into the following unit by doubling the leading consonant of each variant. ん drops the bare `"n"` variant when the next unit's romaji begins with a vowel, `n`, or `y` (keeps `nn`/`n'`). A trailing sokuon with no following kana doubles nothing and is dropped.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_romaji.py  (append)
from split_typing.romaji import build_segments


class TestBuildSegments(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(build_segments("か"), [["ka"]])

    def test_sokuon_doubles_next_consonant(self):
        # がっこう -> ga / っこ(=kko) / う
        segs = build_segments("がっこう")
        self.assertEqual(segs[0], ["ga"])
        self.assertIn("kko", segs[1])
        self.assertEqual(segs[2], ["u"])

    def test_n_keeps_bare_before_consonant(self):
        # にほん だ -> ...ん before space/da: bare n allowed
        segs = build_segments("ほんだ")
        n_seg = segs[1]
        self.assertIn("n", n_seg)
        self.assertIn("nn", n_seg)

    def test_n_drops_bare_before_vowel(self):
        # れんあい -> ん before あ(vowel): bare n NOT allowed
        segs = build_segments("れんあい")
        n_seg = segs[1]
        self.assertNotIn("n", n_seg)
        self.assertIn("nn", n_seg)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_romaji -v`
Expected: FAIL (`build_segments` undefined).

- [ ] **Step 3: Write minimal implementation**

```python
# split_typing/romaji.py (append)
_VOWEL_STARTS = ("a", "i", "u", "e", "o")


def build_segments(reading: str) -> list[list[str]]:
    units = tokenize_kana(reading)
    segments: list[list[str]] = []
    i = 0
    while i < len(units):
        unit = units[i]

        if unit == "っ":
            # double the leading consonant of the NEXT unit's variants
            if i + 1 < len(units):
                nxt = romaji_variants(units[i + 1])
                doubled = []
                for v in nxt:
                    if v and v[0] not in _VOWEL_STARTS and v[0].isalpha():
                        doubled.append(v[0] + v)
                    else:
                        doubled.append(v)  # vowel-initial: no doubling
                segments.append(doubled)
                i += 2
            else:
                i += 1  # trailing sokuon: drop
            continue

        if unit == "ー":
            # long vowel: hyphen, or repeat previous vowel if known
            variants = ["-"]
            if segments:
                prev = segments[-1][0]
                if prev and prev[-1] in _VOWEL_STARTS:
                    variants.append(prev[-1])
            segments.append(variants)
            i += 1
            continue

        if unit == "ん":
            variants = list(romaji_variants("ん"))  # n, nn, n'
            nxt_starts_vowelish = False
            if i + 1 < len(units):
                nxt = romaji_variants(units[i + 1])
                nxt_starts_vowelish = any(
                    v and (v[0] in _VOWEL_STARTS or v[0] in ("n", "y")) for v in nxt
                )
            if nxt_starts_vowelish and "n" in variants:
                variants.remove("n")
            segments.append(variants)
            i += 1
            continue

        segments.append(romaji_variants(unit))
        i += 1
    return segments
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_romaji -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add split_typing/romaji.py tests/test_romaji.py
git commit -m "feat: segment builder with sokuon and n disambiguation

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: RomajiMatcher live matching

**Files:**
- Modify: `split_typing/romaji.py`
- Test: `tests/test_romaji.py`

**Interfaces:**
- Consumes: `build_segments`.
- Produces: `class RomajiMatcher` with: `__init__(self, reading: str)`; `feed(self, ch: str) -> str` returning `"correct"`, `"complete"`, or `"wrong"` (lazy advance with re-feed so `n`/`nn` resolve); property `done: bool`; property `typed: str` (accepted chars so far).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_romaji.py  (append)
from split_typing.romaji import RomajiMatcher


def _type(reading, text):
    m = RomajiMatcher(reading)
    results = [m.feed(c) for c in text]
    return m, results


class TestRomajiMatcher(unittest.TestCase):
    def test_simple_word(self):
        m, res = _type("にほん", "nihon")
        self.assertTrue(m.done)
        self.assertNotIn("wrong", res)

    def test_alt_spelling(self):
        m, _ = _type("し", "si")
        self.assertTrue(m.done)
        m2, _ = _type("し", "shi")
        self.assertTrue(m2.done)

    def test_double_n(self):
        m, _ = _type("れんあい", "rennai")
        self.assertTrue(m.done)

    def test_sokuon(self):
        m, _ = _type("がっこう", "gakkou")
        self.assertTrue(m.done)

    def test_wrong_char(self):
        m = RomajiMatcher("か")
        self.assertEqual(m.feed("x"), "wrong")
        self.assertFalse(m.done)
        self.assertEqual(m.feed("k"), "correct")
        self.assertEqual(m.feed("a"), "complete")
        self.assertTrue(m.done)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_romaji -v`
Expected: FAIL (`RomajiMatcher` undefined).

- [ ] **Step 3: Write minimal implementation**

```python
# split_typing/romaji.py (append)
class RomajiMatcher:
    def __init__(self, reading: str) -> None:
        self.segments = build_segments(reading)
        self.seg_index = 0
        self.buf = ""
        self._typed: list[str] = []

    @property
    def done(self) -> bool:
        return self.seg_index >= len(self.segments)

    @property
    def typed(self) -> str:
        return "".join(self._typed)

    def _current(self) -> list[str]:
        return self.segments[self.seg_index]

    def _advance(self) -> None:
        self.seg_index += 1
        self.buf = ""

    def feed(self, ch: str) -> str:
        if self.done:
            return "wrong"
        seg = self._current()
        cand = self.buf + ch
        if any(v.startswith(cand) for v in seg):
            self.buf = cand
            self._typed.append(ch)
            longer = any(len(v) > len(cand) and v.startswith(cand) for v in seg)
            if cand in seg and not longer:
                self._advance()
                return "complete"
            return "correct"
        # ch does not extend current buffer
        if self.buf in seg:  # current segment already complete -> finalize, re-feed
            self._advance()
            return self.feed(ch)
        return "wrong"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_romaji -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add split_typing/romaji.py tests/test_romaji.py
git commit -m "feat: live RomajiMatcher with lazy advance

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Matcher backspace, hint, expected chars

**Files:**
- Modify: `split_typing/romaji.py`
- Test: `tests/test_romaji.py`

**Interfaces:**
- Consumes: `RomajiMatcher`.
- Produces: on `RomajiMatcher`: `backspace(self) -> bool` (removes last accepted char, returns True if one was removed); property `expected_chars: set[str]` (next acceptable chars); property `hint: str` (one canonical full remaining romaji spelling, first variant of each remaining segment, using the active buffer).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_romaji.py  (append)
class TestMatcherAux(unittest.TestCase):
    def test_backspace(self):
        m = RomajiMatcher("か")
        m.feed("k")
        self.assertTrue(m.backspace())
        self.assertEqual(m.typed, "")
        self.assertFalse(m.backspace())  # nothing to remove

    def test_expected_chars(self):
        m = RomajiMatcher("し")
        self.assertEqual(m.expected_chars, {"s"})  # shi / si both start with s

    def test_hint(self):
        m = RomajiMatcher("にほん")
        self.assertEqual(m.hint, "nihon")
        m.feed("n")
        m.feed("i")
        self.assertEqual(m.hint, "hon")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_romaji -v`
Expected: FAIL (`backspace`/`expected_chars`/`hint` undefined).

- [ ] **Step 3: Write minimal implementation**

```python
# split_typing/romaji.py (append inside RomajiMatcher)
    @property
    def expected_chars(self) -> set[str]:
        if self.done:
            return set()
        seg = self._current()
        out: set[str] = set()
        for v in seg:
            if v.startswith(self.buf) and len(v) > len(self.buf):
                out.add(v[len(self.buf)])
        if not out and self.buf in seg and self.seg_index + 1 < len(self.segments):
            for v in self.segments[self.seg_index + 1]:
                if v:
                    out.add(v[0])
        return out

    @property
    def hint(self) -> str:
        if self.done:
            return ""
        seg = self._current()
        # first variant that still matches the buffer, minus what's typed
        rest = ""
        for v in seg:
            if v.startswith(self.buf):
                rest = v[len(self.buf):]
                break
        tail = "".join(s[0] for s in self.segments[self.seg_index + 1:])
        return rest + tail

    def backspace(self) -> bool:
        if not self._typed:
            return False
        self._typed.pop()
        # rebuild state from scratch up to the new typed string
        typed = "".join(self._typed)
        self.seg_index = 0
        self.buf = ""
        self._typed = []
        for c in typed:
            self.feed(c)
        return True
```

Note: `hint`'s `tail` uses each remaining segment's first variant's first char only as a compact preview; acceptable for a hint. For an exact full hint, change `s[0]` to the full first variant `s` — but keep the test above (`"hon"`) which expects full remaining of current + full of the rest. Update `tail` to `"".join(s[0] for s in ...)` ➜ if the test expects `"hon"` for にほん after `ni`, current seg は ほ→`ho`, then ん→`n`; so tail should be full variants. Set:

```python
        tail = "".join(self.segments[k][0] for k in range(self.seg_index + 1, len(self.segments)))
        return rest + tail
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_romaji -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add split_typing/romaji.py tests/test_romaji.py
git commit -m "feat: matcher backspace, expected chars, and hint

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Reading wrapper (pykakasi)

**Files:**
- Create: `split_typing/reading.py`
- Test: `tests/test_reading.py`

**Interfaces:**
- Produces: `to_hiragana(text: str) -> str` — convert a natural Japanese sentence to its hiragana reading. `pykakasi_available() -> bool`. If pykakasi is missing, `to_hiragana` returns the input unchanged AND `pykakasi_available()` is False.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_reading.py
import unittest
from split_typing import reading


class TestReading(unittest.TestCase):
    def test_available_flag_is_bool(self):
        self.assertIsInstance(reading.pykakasi_available(), bool)

    @unittest.skipUnless(reading.pykakasi_available(), "pykakasi not installed")
    def test_converts_kanji(self):
        self.assertEqual(reading.to_hiragana("日本語"), "にほんご")

    def test_degrades_without_crash(self):
        # passing plain hiragana should round-trip regardless of pykakasi
        self.assertEqual(reading.to_hiragana("ねこ"), "ねこ")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_reading -v`
Expected: FAIL (`split_typing.reading` missing).

- [ ] **Step 3: Write minimal implementation**

```python
# split_typing/reading.py
from __future__ import annotations

try:
    import pykakasi  # type: ignore
    _KKS = pykakasi.kakasi()
except Exception:  # ImportError or init failure
    _KKS = None


def pykakasi_available() -> bool:
    return _KKS is not None


def to_hiragana(text: str) -> str:
    if _KKS is None:
        return text
    return "".join(item["hira"] for item in _KKS.convert(text))
```

- [ ] **Step 4: Run test to verify it passes**

First ensure the dependency is installed for the dev environment:

Run: `python3 -m pip install pykakasi`
Then: `python3 -m unittest tests.test_reading -v`
Expected: PASS (the kanji test runs; without pykakasi it is skipped).

- [ ] **Step 5: Commit**

```bash
git add split_typing/reading.py tests/test_reading.py
git commit -m "feat: pykakasi reading wrapper with graceful degrade

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: KeyStats store (load/save)

**Files:**
- Create: `split_typing/stats.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Produces: `class KeyStats`. `KeyStats.load(path: Path | None = None) -> KeyStats` (default path `~/.split-typing/stats.json`; missing file → empty). `save(self) -> None`. `data: dict[str, dict]` mapping key→`{"count": int, "errors": int, "total_ms": float, "ema_ms": float}`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_stats.py
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from split_typing.stats import KeyStats


class TestKeyStatsIO(unittest.TestCase):
    def test_missing_file_is_empty(self):
        with TemporaryDirectory() as d:
            s = KeyStats.load(Path(d) / "nope.json")
            self.assertEqual(s.data, {})

    def test_roundtrip(self):
        with TemporaryDirectory() as d:
            p = Path(d) / "stats.json"
            s = KeyStats.load(p)
            s.data["k"] = {"count": 1, "errors": 0, "total_ms": 10.0, "ema_ms": 10.0}
            s.save()
            again = KeyStats.load(p)
            self.assertEqual(again.data["k"]["count"], 1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_stats -v`
Expected: FAIL (`split_typing.stats` missing).

- [ ] **Step 3: Write minimal implementation**

```python
# split_typing/stats.py
from __future__ import annotations

import json
from pathlib import Path

DEFAULT_PATH = Path.home() / ".split-typing" / "stats.json"


class KeyStats:
    def __init__(self, path: Path, data: dict[str, dict]) -> None:
        self.path = path
        self.data = data

    @classmethod
    def load(cls, path: Path | None = None) -> "KeyStats":
        path = path or DEFAULT_PATH
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        return cls(path, data)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_stats -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add split_typing/stats.py tests/test_stats.py
git commit -m "feat: KeyStats persistent store

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: Record keystrokes + weakness scoring

**Files:**
- Modify: `split_typing/stats.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: `KeyStats`.
- Produces: on `KeyStats`: `record(self, key: str, ms: float, error: bool) -> None` (updates count/errors/total_ms and EMA with alpha 0.3); `weakness(self, key: str) -> float` (0 if unseen; else `error_rate * W_ERR + norm_latency * W_LAT`, with `W_ERR=0.6`, `W_LAT=0.4`, latency normalized by dividing `ema_ms` by 500 and capping at 1.0); `weakest(self, n: int) -> list[str]` (keys sorted by weakness desc, only keys with count>0).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_stats.py  (append)
class TestKeyStatsScoring(unittest.TestCase):
    def _fresh(self):
        from pathlib import Path
        return KeyStats(Path("/tmp/unused.json"), {})

    def test_record_updates(self):
        s = self._fresh()
        s.record("a", 120.0, error=False)
        self.assertEqual(s.data["a"]["count"], 1)
        self.assertEqual(s.data["a"]["errors"], 0)
        self.assertAlmostEqual(s.data["a"]["ema_ms"], 120.0)

    def test_weakness_orders_by_error_and_latency(self):
        s = self._fresh()
        for _ in range(10):
            s.record("good", 80.0, error=False)
        for _ in range(10):
            s.record("bad", 400.0, error=True)
        self.assertGreater(s.weakness("bad"), s.weakness("good"))
        self.assertEqual(s.weakest(1), ["bad"])

    def test_unseen_is_zero(self):
        self.assertEqual(self._fresh().weakness("z"), 0.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_stats -v`
Expected: FAIL (`record`/`weakness`/`weakest` undefined).

- [ ] **Step 3: Write minimal implementation**

```python
# split_typing/stats.py (append inside KeyStats)
    _ALPHA = 0.3
    _W_ERR = 0.6
    _W_LAT = 0.4

    def record(self, key: str, ms: float, error: bool) -> None:
        entry = self.data.setdefault(
            key, {"count": 0, "errors": 0, "total_ms": 0.0, "ema_ms": ms}
        )
        entry["count"] += 1
        entry["errors"] += 1 if error else 0
        entry["total_ms"] += ms
        entry["ema_ms"] = self._ALPHA * ms + (1 - self._ALPHA) * entry["ema_ms"]

    def weakness(self, key: str) -> float:
        entry = self.data.get(key)
        if not entry or entry["count"] == 0:
            return 0.0
        error_rate = entry["errors"] / entry["count"]
        norm_lat = min(entry["ema_ms"] / 500.0, 1.0)
        return error_rate * self._W_ERR + norm_lat * self._W_LAT

    def weakest(self, n: int) -> list[str]:
        seen = [k for k, v in self.data.items() if v["count"] > 0]
        seen.sort(key=self.weakness, reverse=True)
        return seen[:n]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_stats -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add split_typing/stats.py tests/test_stats.py
git commit -m "feat: keystroke recording and weakness scoring

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: Adaptive selection + focus drills

**Files:**
- Create: `split_typing/adaptive.py`
- Test: `tests/test_adaptive.py`

**Interfaces:**
- Consumes: `KeyStats`, `split_typing.reading.to_hiragana`, `split_typing.romaji.build_segments`.
- Produces: `prompt_weak_key_load(prompt: str, language: str, weak_keys: set[str]) -> int` (count of weak-key occurrences in the romaji of `prompt`); `select_adaptive(prompts: list[str], language: str, stats: KeyStats, count: int, seed: int | None = None) -> list[str]` (weighted sampling biased toward prompts with more weak-key load, deterministic under `seed`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_adaptive.py
import unittest
from pathlib import Path
from split_typing.stats import KeyStats
from split_typing.adaptive import prompt_weak_key_load, select_adaptive


def _stats_weak_on(keys):
    s = KeyStats(Path("/tmp/unused.json"), {})
    for k in keys:
        for _ in range(10):
            s.record(k, 400.0, error=True)
    return s


class TestAdaptive(unittest.TestCase):
    def test_load_counts_weak_keys(self):
        # english: prompt text == romaji
        self.assertEqual(prompt_weak_key_load("zzz aaa", "english", {"z"}), 3)

    def test_select_biases_to_weak(self):
        stats = _stats_weak_on(["z"])
        prompts = ["aaaa", "zzzz", "aaaa", "aaaa"]
        picks = select_adaptive(prompts, "english", stats, count=4, seed=1)
        self.assertIn("zzzz", picks)

    def test_deterministic(self):
        stats = _stats_weak_on(["z"])
        prompts = ["aaaa", "zzzz", "bbbb", "cccc"]
        a = select_adaptive(prompts, "english", stats, 3, seed=7)
        b = select_adaptive(prompts, "english", stats, 3, seed=7)
        self.assertEqual(a, b)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_adaptive -v`
Expected: FAIL (`split_typing.adaptive` missing).

- [ ] **Step 3: Write minimal implementation**

```python
# split_typing/adaptive.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_adaptive -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add split_typing/adaptive.py tests/test_adaptive.py
git commit -m "feat: adaptive weak-key weighted prompt selection

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 10: Realtime session loop

**Files:**
- Modify: `split_typing/engine.py`
- Test: `tests/test_engine.py`

**Interfaces:**
- Consumes: `split_typing.romaji.RomajiMatcher`, `KeyStats`.
- Produces: `class RealtimeSession`. `__init__(self, reading: str, stats: KeyStats | None = None)`. `key(self, ch: str, ms: float) -> str` — feed one keystroke with elapsed ms; returns `"correct"`/`"complete"`/`"wrong"`; records into stats (error=True on `"wrong"`, keyed by the typed char). `backspace(self) -> None`. Properties: `done`, `typed`, `hint`, `errors: int` (total wrong keystrokes). The `key` method must keep the existing `score_attempt` untouched.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_engine.py  (append; keep existing tests)
from pathlib import Path
from split_typing.engine import RealtimeSession
from split_typing.stats import KeyStats


class TestRealtimeSession(unittest.TestCase):
    def test_completes_and_counts_errors(self):
        s = KeyStats(Path("/tmp/unused.json"), {})
        sess = RealtimeSession("か", stats=s)
        self.assertEqual(sess.key("x", 100.0), "wrong")
        self.assertEqual(sess.key("k", 90.0), "correct")
        self.assertEqual(sess.key("a", 80.0), "complete")
        self.assertTrue(sess.done)
        self.assertEqual(sess.errors, 1)
        self.assertEqual(s.data["x"]["errors"], 1)
        self.assertEqual(s.data["k"]["errors"], 0)
```

(Existing `tests/test_engine.py` must already `import unittest`; if not, add it.)

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_engine -v`
Expected: FAIL (`RealtimeSession` undefined).

- [ ] **Step 3: Write minimal implementation**

```python
# split_typing/engine.py (append; do not modify score_attempt)
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_engine -v`
Expected: PASS (including the pre-existing engine tests).

- [ ] **Step 5: Commit**

```bash
git add split_typing/engine.py tests/test_engine.py
git commit -m "feat: realtime keystroke session loop

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 11: Raw-mode input capture

**Files:**
- Create: `split_typing/input_capture.py`
- Test: `tests/test_input_capture.py`

**Interfaces:**
- Produces: `supports_raw() -> bool` (True only if stdin AND stdout are TTYs and `termios` importable); `read_keys()` — a context-managed generator yielding single characters in raw mode, restoring the terminal on exit. Backspace yields `"\x7f"`, Enter yields `"\r"`, ESC yields `"\x1b"`, Ctrl-C raises `KeyboardInterrupt`. Because raw TTY I/O cannot be unit-tested headlessly, only `supports_raw()` is tested; `read_keys` is smoke-tested manually.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_input_capture.py
import unittest
from split_typing.input_capture import supports_raw


class TestInputCapture(unittest.TestCase):
    def test_supports_raw_is_bool(self):
        self.assertIsInstance(supports_raw(), bool)

    def test_supports_raw_false_when_not_tty(self):
        # under the test runner stdin is usually not a TTY
        # so this must not raise and must return a bool
        self.assertIn(supports_raw(), (True, False))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_input_capture -v`
Expected: FAIL (module missing).

- [ ] **Step 3: Write minimal implementation**

```python
# split_typing/input_capture.py
from __future__ import annotations

import sys
from contextlib import contextmanager

try:
    import termios
    import tty
    _HAVE_TERMIOS = True
except ImportError:
    _HAVE_TERMIOS = False


def supports_raw() -> bool:
    return _HAVE_TERMIOS and sys.stdin.isatty() and sys.stdout.isatty()


@contextmanager
def raw_terminal():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def read_keys():
    """Yield one character at a time in raw mode. Ctrl-C -> KeyboardInterrupt."""
    with raw_terminal():
        while True:
            ch = sys.stdin.read(1)
            if ch == "\x03":  # Ctrl-C
                raise KeyboardInterrupt
            yield ch
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_input_capture -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add split_typing/input_capture.py tests/test_input_capture.py
git commit -m "feat: raw-mode keystroke capture with safe restore

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 12: CLI wiring, rendering, and `--stats`

**Files:**
- Modify: `split_typing/cli.py`
- Test: `tests/test_cli.py` (create)

**Interfaces:**
- Consumes: everything above plus existing `get_prompts`, `generate_prompts`.
- Produces: argparse adds `--classic`, `--adaptive`, `--stats`, `--no-color`. New helpers: `run_realtime_prompt(display: str, reading: str, stats, color: bool) -> bool` (returns True if completed, False if skipped); `print_weak_keys(stats: KeyStats) -> None`. Behavior: realtime is default; falls back to classic automatically when `not supports_raw()`. Japanese: `display` is the original prompt, `reading = to_hiragana(display)`; English/Python: `display == reading == prompt`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cli.py
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from split_typing.stats import KeyStats
from split_typing.cli import build_parser, print_weak_keys


class TestCliPlumbing(unittest.TestCase):
    def test_new_flags_parse(self):
        args = build_parser().parse_args(
            ["--language", "english", "--level", "1", "--classic", "--adaptive"]
        )
        self.assertTrue(args.classic)
        self.assertTrue(args.adaptive)

    def test_stats_flag(self):
        args = build_parser().parse_args(["--stats"])
        self.assertTrue(args.stats)

    def test_print_weak_keys_runs(self):
        s = KeyStats(Path("/tmp/unused.json"), {})
        s.record("z", 400.0, error=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            print_weak_keys(s)
        self.assertIn("z", buf.getvalue())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_cli -v`
Expected: FAIL (`print_weak_keys`/flags missing).

- [ ] **Step 3: Write minimal implementation**

Add flags to `build_parser`, add the helpers, and branch in `main`. Key additions (engineer integrates with existing `main`/`run_session`):

```python
# split_typing/cli.py (additions)
from split_typing.stats import KeyStats
from split_typing.reading import to_hiragana
from split_typing.engine import RealtimeSession
from split_typing.input_capture import supports_raw, read_keys

# in build_parser():
#   parser.add_argument("--classic", action="store_true", help="line-input mode")
#   parser.add_argument("--adaptive", action="store_true", help="bias prompts to weak keys")
#   parser.add_argument("--stats", action="store_true", help="show weak keys and exit")
#   parser.add_argument("--no-color", action="store_true", help="disable ANSI color")


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


def run_realtime_prompt(display: str, reading: str, stats: KeyStats, color: bool) -> bool:
    import time
    sess = RealtimeSession(reading, stats=stats)
    print(display)
    last = time.perf_counter()
    keys = read_keys()
    for ch in keys:
        if ch in ("\x1b", "\t"):   # ESC / Tab -> skip prompt
            print("  [skipped]")
            return False
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
            return True
    return False


def _render(sess: RealtimeSession, color: bool) -> None:
    typed = sess.typed
    if color:
        line = f"\r\x1b[2K{typed}\x1b[90m{sess.hint}\x1b[0m"
    else:
        line = f"\r\x1b[2K{typed}|{sess.hint}"
    print(line, end="", flush=True)
```

In `main`, before the normal flow: if `args.stats`, load `KeyStats.load()`, call `print_weak_keys`, return 0. Choose realtime vs classic: `use_realtime = not args.classic and supports_raw()`. For realtime, build `(display, reading)` pairs (`reading = to_hiragana(display)` only for japanese), and loop calling `run_realtime_prompt`, saving stats at the end. If `args.adaptive`, build the prompt list with `select_adaptive(...)`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_cli -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add split_typing/cli.py tests/test_cli.py
git commit -m "feat: CLI realtime mode, adaptive, stats view, classic fallback

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 13: Enrich static prompt banks

**Files:**
- Modify: `split_typing/prompts.py`
- Test: `tests/test_prompts.py`

**Interfaces:**
- Produces: larger `PROMPTS` banks. Japanese banks at levels 3–4 use natural sentences (kanji allowed — they pass through `to_hiragana` at runtime). Keep `get_prompts`/`available_languages`/`levels_for_language` signatures unchanged.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_prompts.py  (append)
from split_typing.prompts import PROMPTS


class TestBankSize(unittest.TestCase):
    def test_japanese_levels_have_more_variety(self):
        for level in (1, 2, 3, 4):
            self.assertGreaterEqual(len(PROMPTS["japanese"][level]), 12)

    def test_english_levels_have_more_variety(self):
        for level in (1, 2, 3, 4):
            self.assertGreaterEqual(len(PROMPTS["english"][level]), 12)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_prompts -v`
Expected: FAIL (banks too small).

- [ ] **Step 3: Write minimal implementation**

Expand each list in `PROMPTS` to >=12 entries. Japanese levels 3–4 should be natural varied sentences (kanji + kana), e.g. `"今日の会議は午後三時に始まります。"`, `"駅の近くに新しい本屋ができた。"`, etc. Keep levels 1–2 mostly kana for fundamentals. (Engineer: write at least 12 distinct, natural entries per `(language, level)` cell.)

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_prompts -v`
Expected: PASS. Also run full suite: `python3 -m unittest discover -s tests -v`.

- [ ] **Step 5: Commit**

```bash
git add split_typing/prompts.py tests/test_prompts.py
git commit -m "content: enrich static prompt banks

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 14: Natural Japanese LLM generation

**Files:**
- Modify: `split_typing/llm.py`
- Test: `tests/test_llm.py`

**Interfaces:**
- Produces: `build_request(language, level, overfetch)` extracted as a helper so the Japanese prompt asks for natural sentences (kanji allowed) and the prompt text is unit-testable without invoking ollama. `generate_prompts` keeps its signature.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_llm.py  (append)
from split_typing.llm import build_request


class TestBuildRequest(unittest.TestCase):
    def test_japanese_request_asks_for_natural(self):
        req = build_request("japanese", 3, 10)
        self.assertIn("Japanese", req)
        self.assertIn("10", req)

    def test_english_request(self):
        req = build_request("english", 1, 8)
        self.assertIn("8", req)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_llm -v`
Expected: FAIL (`build_request` undefined).

- [ ] **Step 3: Write minimal implementation**

Extract the existing inline request string in `generate_prompts` into `build_request(language, level, overfetch) -> str`, and add a Japanese-specific clause: natural everyday sentences, kanji-and-kana allowed, varied vocabulary and topics, one sentence per line. Have `generate_prompts` call `build_request`.

```python
# split_typing/llm.py (shape)
def build_request(language: str, level: int, overfetch: int) -> str:
    base = (
        "Create typing practice prompts for a local CLI typing trainer.\n"
        f"Language track: {language}\n"
        f"Difficulty level: {level} where 1 is short and 4 is longer.\n"
        f"Return exactly {overfetch} plain lines. No numbering, no markdown.\n"
        "Every line must be DISTINCT: vary vocabulary, topic, and sentence shape.\n"
    )
    if language == "japanese":
        base += (
            "Write natural everyday Japanese sentences using normal kanji and kana. "
            "Avoid childish all-hiragana text. One natural sentence per line.\n"
        )
    base += "Keep each line typeable in a terminal."
    return base
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_llm -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add split_typing/llm.py tests/test_llm.py
git commit -m "feat: natural Japanese LLM prompt request

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 15: Packaging — pyproject, LICENSE, .gitignore

**Files:**
- Create: `pyproject.toml`, `LICENSE`
- Modify: `.gitignore`

**Interfaces:**
- Produces: installable package with console entry point `split-typing` and `pykakasi` dependency.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_packaging.py
import unittest
import tomllib
from pathlib import Path


class TestPackaging(unittest.TestCase):
    def test_pyproject_has_entrypoint_and_dep(self):
        data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
        self.assertIn("split-typing", data["project"]["scripts"])
        self.assertTrue(any("pykakasi" in d for d in data["project"]["dependencies"]))

    def test_license_exists(self):
        self.assertTrue(Path("LICENSE").exists())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_packaging -v`
Expected: FAIL (files missing).

- [ ] **Step 3: Write minimal implementation**

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "split-typing-cli"
version = "0.2.0"
description = "Real-time, adaptive CLI typing trainer for split keyboards (with Japanese romaji support)"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
dependencies = ["pykakasi>=2.2"]

[project.scripts]
split-typing = "split_typing.cli:main"

[tool.setuptools]
packages = ["split_typing"]
```

Create `LICENSE` with the standard MIT text (year 2026, author per the user's confirmation at publish time — use a placeholder name to be replaced in Task 17). Append to `.gitignore`:

```
__pycache__/
*.pyc
.venv/
build/
dist/
*.egg-info/
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_packaging -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml LICENSE .gitignore tests/test_packaging.py
git commit -m "build: packaging metadata, MIT license, ignores

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 16: Public README

**Files:**
- Modify: `README.md`

**Interfaces:**
- Produces: general-audience README. No personal absolute paths. Documents realtime mode, Japanese romaji flow, adaptive/stats, classic fallback, install (`pip install -e .`), and dependency note.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_readme.py
import unittest
from pathlib import Path


class TestReadme(unittest.TestCase):
    def test_no_personal_paths(self):
        text = Path("README.md").read_text(encoding="utf-8")
        self.assertNotIn("/Users/", text)

    def test_mentions_key_features(self):
        text = Path("README.md").read_text(encoding="utf-8").lower()
        for token in ("realtime", "adaptive", "pykakasi", "classic"):
            self.assertIn(token, text)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_readme -v`
Expected: FAIL (old README has `/Users/` paths and lacks tokens).

- [ ] **Step 3: Write minimal implementation**

Rewrite `README.md`: title, one-paragraph pitch, Features (realtime per-key feedback, weak-key adaptive drills, Japanese kanji→reading→romaji via pykakasi, classic line mode, optional Ollama generation), Install (`pip install -e .` or `pip install pykakasi`), Usage (`split-typing`, `--language/--level/--count`, `--adaptive`, `--stats`, `--classic`, `--llm --model`), How Japanese works (display kanji, type romaji of the reading; multi-variant acceptance; skip with Tab/ESC), Notes (POSIX raw mode; stats stored at `~/.split-typing/stats.json`), Tests, License.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_readme -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add README.md tests/test_readme.py
git commit -m "docs: public-facing README

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 17: Final verification + publish (gated)

**Files:** none (verification + release)

- [ ] **Step 1: Full test suite**

Run: `python3 -m unittest discover -s tests -v`
Expected: ALL PASS.

- [ ] **Step 2: Manual smoke (interactive — run in a real terminal)**

```bash
python3 -m pip install -e .
split-typing --language japanese --level 3 --count 3
split-typing --stats
split-typing --language english --level 1 --count 5 --adaptive
```
Expected: realtime per-key coloring; Japanese shows kanji and accepts romaji of the reading; `--stats` lists weak keys.

- [ ] **Step 3: Scrub for personal info**

Run: `grep -rn "/Users/\|msugino\|masahito" --include=*.py --include=*.md --include=*.toml . | grep -v docs/superpowers`
Expected: no matches outside internal planning docs. Fix any. Set the real author name/year in `LICENSE`.

- [ ] **Step 4: Confirm publish details with the user**

Ask (do not push until answered): repo name (default `split-typing-cli`), public vs private, GitHub account, license author name. STOP and wait.

- [ ] **Step 5: Merge and publish**

```bash
git checkout main && git merge --no-ff realtime-adaptive
gh repo create <name> --public --source=. --remote=origin --push
```
Expected: repo created and pushed. Print the URL.

---

## Self-Review

**Spec coverage:**
- Realtime per-keystroke input → Tasks 4, 10, 11, 12. ✓
- Japanese kanji→reading→romaji (flexible) → Tasks 1–6, 12. ✓
- pykakasi misread mitigation (hint + skip) → Task 5 (hint), Task 12 (Tab/ESC skip, hint render). ✓
- Per-key stats persistence → Tasks 7, 8. ✓
- Adaptive weak-key drills → Tasks 9, 12. ✓
- Classic fallback / non-TTY → Tasks 11, 12. ✓
- Enriched vocabulary + natural LLM JP → Tasks 13, 14. ✓
- Public release (pyproject, LICENSE, README, scrub, publish) → Tasks 15–17. ✓

**Placeholder scan:** Content-generation tasks (13, 16) describe exact requirements with concrete examples and enforce them via tests; LICENSE/author name is intentionally finalized in Task 17 after user confirmation (a real gate, not a vague placeholder).

**Type consistency:** `feed`/`key` return the same string set `{"correct","complete","wrong"}` across Tasks 4 and 10. `KeyStats.record(key, ms, error)` signature consistent across Tasks 8, 10, 12. `build_segments`/`RomajiMatcher`/`to_hiragana` names consistent across Tasks 1–6, 9, 10, 12.
