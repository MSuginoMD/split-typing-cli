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
