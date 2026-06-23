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


ROMAJI_TABLE: dict[str, list[str]] = {
    # gojuon (5x5)
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
    # dakuten (voiced)
    "が": ["ga"], "ぎ": ["gi"], "ぐ": ["gu"], "げ": ["ge"], "ご": ["go"],
    "ざ": ["za"], "じ": ["ji", "zi"], "ず": ["zu"], "ぜ": ["ze"], "ぞ": ["zo"],
    "だ": ["da"], "ぢ": ["di", "ji"], "づ": ["du", "zu"], "で": ["de"], "ど": ["do"],
    "ば": ["ba"], "び": ["bi"], "ぶ": ["bu"], "べ": ["be"], "ぼ": ["bo"],
    # handakuten (semi-voiced)
    "ぱ": ["pa"], "ぴ": ["pi"], "ぷ": ["pu"], "ぺ": ["pe"], "ぽ": ["po"],
    # youon (i-column + small-y)
    "きゃ": ["kya"], "きゅ": ["kyu"], "きょ": ["kyo"],
    "しゃ": ["sha", "sya"], "しゅ": ["shu", "syu"], "しょ": ["sho", "syo"],
    "ちゃ": ["cha", "tya", "cya"], "ちゅ": ["chu", "tyu", "cyu"], "ちょ": ["cho", "tyo", "cyo"],
    "にゃ": ["nya"], "にゅ": ["nyu"], "にょ": ["nyo"],
    "ひゃ": ["hya"], "ひゅ": ["hyu"], "ひょ": ["hyo"],
    "みゃ": ["mya"], "みゅ": ["myu"], "みょ": ["myo"],
    "りゃ": ["rya"], "りゅ": ["ryu"], "りょ": ["ryo"],
    # dakuten youon
    "ぎゃ": ["gya"], "ぎゅ": ["gyu"], "ぎょ": ["gyo"],
    "じゃ": ["ja", "zya", "jya"], "じゅ": ["ju", "zyu", "jyu"], "じょ": ["jo", "zyo", "jyo"],
    "ぢゃ": ["dya", "jya"], "ぢゅ": ["dyu", "jyu"], "ぢょ": ["dyo", "jyo"],
    "びゃ": ["bya"], "びゅ": ["byu"], "びょ": ["byo"],
    # handakuten youon
    "ぴゃ": ["pya"], "ぴゅ": ["pyu"], "ぴょ": ["pyo"],
    # ふ combinations (small vowels)
    "ふぁ": ["fa"], "ふぃ": ["fi"], "ふぇ": ["fe"], "ふぉ": ["fo"],
    # small standalone vowels (rare)
    "ぁ": ["la", "xa"], "ぃ": ["li", "xi"], "ぅ": ["lu", "xu"],
    "ぇ": ["le", "xe"], "ぉ": ["lo", "xo"],
}


def romaji_variants(unit: str) -> list[str]:
    if unit in ROMAJI_TABLE:
        return list(ROMAJI_TABLE[unit])
    return [unit]  # pass-through: space, punctuation, ascii


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


class RomajiMatcher:
    def __init__(self, reading: str) -> None:
        self.segments = build_segments(reading)
        self.seg_index = 0
        self.buf = ""
        self._typed: list[str] = []
        self._just_completed_n = False  # last segment completed by a bare "ん"=n

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
            # Absorb a redundant trailing "n" so word-final ん typed as "nn" is OK.
            if ch == "n" and self._just_completed_n:
                self._just_completed_n = False
                self._typed.append(ch)
                return "complete"
            self._just_completed_n = False
            return "wrong"
        seg = self._current()
        cand = self.buf + ch
        if any(v.startswith(cand) for v in seg):
            self.buf = cand
            self._typed.append(ch)
            is_last = self.seg_index == len(self.segments) - 1
            longer = any(len(v) > len(cand) and v.startswith(cand) for v in seg)
            if cand in seg and (not longer or is_last):
                self._just_completed_n = cand == "n"
                self._advance()
                return "complete"
            return "correct"
        # ch does not extend current buffer
        if self.buf in seg:  # current segment already complete -> finalize, re-feed
            self._advance()
            return self.feed(ch)
        return "wrong"

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
        tail = "".join(self.segments[k][0] for k in range(self.seg_index + 1, len(self.segments)))
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
