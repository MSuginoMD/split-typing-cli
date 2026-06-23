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
    "ちゃ": ["cha", "tya"], "ちゅ": ["chu", "tyu"], "ちょ": ["cho", "tyo"],
    "にゃ": ["nya"], "にゅ": ["nyu"], "にょ": ["nyo"],
    "ひゃ": ["hya"], "ひゅ": ["hyu"], "ひょ": ["hyo"],
    "みゃ": ["mya"], "みゅ": ["myu"], "みょ": ["myo"],
    "りゃ": ["rya"], "りゅ": ["ryu"], "りょ": ["ryo"],
    # dakuten youon
    "ぎゃ": ["gya"], "ぎゅ": ["gyu"], "ぎょ": ["gyo"],
    "じゃ": ["ja", "zya", "jya"], "じゅ": ["ju", "zyu", "jyu"], "じょ": ["jo", "zyo", "jyo"],
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
