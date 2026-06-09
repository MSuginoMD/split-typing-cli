from __future__ import annotations

import random


PROMPTS: dict[str, dict[int, tuple[str, ...]]] = {
    "english": {
        1: (
            "quiet",
            "split",
            "finger",
            "return",
            "space",
            "control",
            "shift",
            "layout",
        ),
        2: (
            "left hand right hand",
            "type the home row",
            "hold shift then slash",
            "space enter backspace",
            "quick brown fox",
            "practice small bursts",
        ),
        3: (
            "The split keyboard rewards relaxed hands and steady rhythm.",
            "Move slowly at first, then let accuracy pull speed forward.",
            "Use the thumb keys without looking down at the board.",
            "Short sessions help the new layout settle into memory.",
        ),
        4: (
            "A split keyboard feels strange because each hand has a smaller world to manage. Keep your wrists quiet, trust the layers, and let the motion become boring.",
            "Accuracy matters more than speed during adaptation. If a symbol layer feels awkward, repeat it slowly until the sequence is no longer a decision.",
        ),
    },
    "japanese": {
        1: (
            "て",
            "かな",
            "にほん",
            "れんしゅう",
            "みぎて",
            "ひだりて",
            "おやゆび",
            "はいれつ",
        ),
        2: (
            "ひだりて と みぎて",
            "ゆっくり ただしく",
            "おやゆびで すぺーす",
            "きごうも れんしゅう",
            "みないで うつ",
            "みじかく くりかえす",
        ),
        3: (
            "ぶんりキーボードでは、てのいどうをちいさくすることがたいせつです。",
            "さいしょははやさよりも、まちがえないリズムをつくります。",
            "おやゆびキーとレイヤーにすこしずつなれていきます。",
            "ながいぶんは、いきつぎをするようにくぎってうちます。",
        ),
        4: (
            "あたらしいはいれつになれるには、まいにちすこしずつおなじうごきをくりかえすのがいちばんです。ゆびのばしょをさがすじかんをへらして、リズムをたもってください。",
            "ぶんりキーボードはさいしょだけむずかしくかんじますが、てくびをひらいてうてるので、なれるとからだのふたんをへらせます。",
        ),
    },
    "python": {
        1: (
            "def",
            "return",
            "import",
            "list",
            "dict",
            "range",
            "print",
            "pytest",
        ),
        2: (
            "def main():",
            "for item in items:",
            "if value is None:",
            "return result",
            "print(name.lower())",
            "items.append(value)",
        ),
        3: (
            "def normalize(text: str) -> str:",
            "users = [user for user in users if user.active]",
            "with open(path, encoding=\"utf-8\") as handle:",
            "total = sum(row.amount for row in rows)",
        ),
        4: (
            "def score(expected: str, actual: str) -> float:\n    matches = sum(a == b for a, b in zip(expected, actual))\n    return matches / max(len(expected), 1)",
            "for index, prompt in enumerate(prompts, start=1):\n    typed = input(f\"{index}> \")\n    print(score_attempt(prompt, typed, seconds=3.0))",
        ),
    },
}


def available_languages() -> tuple[str, ...]:
    return tuple(PROMPTS)


def levels_for_language(language: str) -> tuple[int, ...]:
    if language not in PROMPTS:
        raise ValueError(f"unknown language: {language}")
    return tuple(PROMPTS[language])


def get_prompts(language: str, level: int, count: int, seed: int | None = None) -> list[str]:
    if language not in PROMPTS:
        raise ValueError(f"unknown language: {language}")
    if level not in PROMPTS[language]:
        raise ValueError(f"unknown level for {language}: {level}")
    if count < 1:
        return []

    source = list(PROMPTS[language][level])
    rng = random.Random(seed)
    if count <= len(source):
        rng.shuffle(source)
        return source[:count]
    return [rng.choice(source) for _ in range(count)]
