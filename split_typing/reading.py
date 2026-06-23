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
