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
            "thumb",
            "layer",
            "wrist",
            "chord",
            "tap",
            "hold",
            "home",
        ),
        2: (
            "left hand right hand",
            "type the home row",
            "hold shift then slash",
            "space enter backspace",
            "quick brown fox",
            "practice small bursts",
            "reach for the tab key",
            "use thumb for space",
            "keep wrists relaxed",
            "roll fingers gently",
            "find the home position",
            "alternate hands smoothly",
            "press and release cleanly",
        ),
        3: (
            "The split keyboard rewards relaxed hands and steady rhythm.",
            "Move slowly at first, then let accuracy pull speed forward.",
            "Use the thumb keys without looking down at the board.",
            "Short sessions help the new layout settle into memory.",
            "Each layer adds power once the base row feels natural.",
            "Keep your elbows at roughly ninety degrees while typing.",
            "Muscle memory builds faster when you repeat the same drills.",
            "Look at the screen, not the keys, from the very first session.",
            "A quiet keystroke usually means the finger landed well.",
            "Typing slowly on purpose is one of the hardest disciplines.",
            "The modifier keys live under your thumbs on a split board.",
            "Consistent finger placement is worth more than raw speed.",
        ),
        4: (
            "A split keyboard feels strange because each hand has a smaller world to manage. Keep your wrists quiet, trust the layers, and let the motion become boring.",
            "Accuracy matters more than speed during adaptation. If a symbol layer feels awkward, repeat it slowly until the sequence is no longer a decision.",
            "The goal of a custom layout is to reduce lateral wrist movement so that your fingers stay close to home. Once you feel that reduction, returning to a standard board feels cramped.",
            "Typing practice is most effective in short, focused bursts. Ten minutes of deliberate drilling beats an hour of sloppy fast work because bad habits compound faster than good ones.",
            "Column-stagger columns keep each finger on a vertical axis. The ring and pinky columns are angled slightly inward, which means your reaching motions become shorter and more predictable over time.",
            "Holding a modifier with one hand while tapping a key with the other is the muscle-memory pattern that underlies every keyboard shortcut. A split board makes that cross-hand division explicit and natural.",
            "When you first switch layouts, your measured words-per-minute will drop dramatically. Accept this as the cost of learning and measure progress in errors-per-line rather than raw speed.",
            "Every key that lives under a thumb rather than a pinky is a key that your strongest digit handles instead of your weakest. Over thousands of keystrokes the ergonomic difference accumulates.",
            "Setting a timer for fifteen minutes of targeted practice and then stopping is more sustainable than open-ended sessions. Fatigue degrades form, and degraded form reinforces wrong movements.",
            "A programmable firmware lets you move any key to any position, but the freedom can become paralyzing. Start with a sensible default, use it for a month, and only then adjust what clearly bothers you.",
            "The return key on a standard board sits awkwardly far from the home row, which is why so many split boards move it to a thumb cluster. A few days of adjustment and you will wonder how you managed before.",
            "Good typing posture is invisible in the sense that you stop noticing your hands. When discomfort appears it is usually a sign that something in the angle, height, or reach has crept out of alignment.",
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
            "ゆび",
            "きほん",
            "もじ",
            "たいぷ",
            "りょうて",
            "ほーむ",
            "きー",
        ),
        2: (
            "ひだりて と みぎて",
            "ゆっくり ただしく",
            "おやゆびで すぺーす",
            "きごうも れんしゅう",
            "みないで うつ",
            "みじかく くりかえす",
            "ほーむ ぽじしょん",
            "りょうて を つかう",
            "なれると はやくなる",
            "まず きほんから",
            "しせいを ただしく",
            "えらーを へらす",
            "すこしずつ すすむ",
        ),
        3: (
            "今日の会議は午後三時に始まります。",
            "駅前に新しい喫茶店ができたので寄ってみた。",
            "分離キーボードに慣れると元の配列には戻れない。",
            "毎朝少しだけ練習を続けるのが上達の近道だ。",
            "画面を見ながら打つ習慣を最初から身につけよう。",
            "正確さを保ちながらリズムを一定に保つことが大切です。",
            "親指キーにエンターを割り当てると手の移動が減る。",
            "新しい配列を覚えるときは焦らず丁寧に繰り返す。",
            "手首をリラックスさせると長時間でも疲れにくくなる。",
            "レイヤー機能を使えばキーボードの可能性が広がる。",
            "短い文章から始めて徐々に長さを増やしていきましょう。",
            "ミスタイプが増えてきたら一度スピードを落とす。",
            "指の置き場所を意識するだけで精度が上がってくる。",
        ),
        4: (
            "分離キーボードを使い始めてしばらくは入力速度が下がるが、慣れてくると手首への負担が明らかに減り、長時間作業しても疲れにくくなる。",
            "ブラインドタッチを身につけるには、最初の一週間は速さを追わず、キーの位置だけに集中する練習が効果的だと言われている。",
            "プログラマブルなファームウェアを使えばホームポジションをほとんど崩さずにすべての操作を完結させることもできる。",
            "新しい入力配列を習得するときは、完璧に覚えてから試すより、不完全な状態でも実際に使い続けるほうが記憶に定着しやすい。",
            "キーボードの打鍵音が小さくなってきたら、指が正確にキーの中心を捉えられている証拠だと考えてよい。",
            "長文を打つときは文節ごとに少し間を置き、次の単語を頭の中で準備してから指を動かすと全体のテンポが乱れにくい。",
            "毎日十五分の集中練習を一か月続けると、ほとんどの人が体感できるほど指の動きが滑らかになってくる。",
            "キーマップをカスタマイズしすぎると他のキーボードで全く打てなくなるため、標準から大きく外れない範囲で調整するのが無難だ。",
            "手の小さい人にとって分離型は特に恩恵が大きく、小指が不自然に伸びる場面が劇的に減るのが実感できるはずだ。",
            "親指クラスターにシフトやレイヤー切替を置くと小指の使用頻度が下がり、腱鞘炎のリスクを減らせると言われている。",
            "タイピング練習アプリで計測するより、実際の作業中に意識してフォームを正す方が実用的な速度向上につながりやすい。",
            "配列を変えるときは一気にすべてを移行するより、まず最も頻度の高いキーだけを変えて慣らすという段階的な方法が挫折しにくい。",
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
            "class",
            "async",
            "yield",
            "raise",
            "lambda",
            "assert",
            "global",
        ),
        2: (
            "def main():",
            "for item in items:",
            "if value is None:",
            "return result",
            "print(name.lower())",
            "items.append(value)",
            "x = int(input())",
            "raise ValueError(msg)",
            "assert n > 0",
            "yield from gen",
            "key, val = pair",
            "path = Path(src)",
            "count += 1",
        ),
        3: (
            "def normalize(text: str) -> str:",
            "users = [user for user in users if user.active]",
            "with open(path, encoding=\"utf-8\") as handle:",
            "total = sum(row.amount for row in rows)",
            "result = {k: v for k, v in mapping.items() if v}",
            "logging.basicConfig(level=logging.INFO)",
            "data = json.loads(response.text)",
            "if not isinstance(value, (int, float)):",
            "parser.add_argument(\"--output\", type=Path)",
            "df = pd.read_csv(src, encoding=\"utf-8\")",
            "async def fetch(url: str) -> bytes:",
            "tokens = text.strip().split(maxsplit=1)",
            "@dataclass\nclass Config:",
        ),
        4: (
            "def score(expected: str, actual: str) -> float:\n    matches = sum(a == b for a, b in zip(expected, actual))\n    return matches / max(len(expected), 1)",
            "for index, prompt in enumerate(prompts, start=1):\n    typed = input(f\"{index}> \")\n    print(score_attempt(prompt, typed, seconds=3.0))",
            "def retry(fn, *, attempts: int = 3, delay: float = 1.0):\n    for i in range(attempts):\n        try:\n            return fn()\n        except Exception:\n            if i == attempts - 1:\n                raise\n            time.sleep(delay)",
            "class RingBuffer(Generic[T]):\n    def __init__(self, capacity: int) -> None:\n        self._buf: deque[T] = deque(maxlen=capacity)\n    def push(self, item: T) -> None:\n        self._buf.append(item)",
            "def parse_args() -> argparse.Namespace:\n    p = argparse.ArgumentParser()\n    p.add_argument(\"src\", type=Path)\n    p.add_argument(\"--level\", type=int, default=1)\n    return p.parse_args()",
            "results = await asyncio.gather(\n    *[fetch(url) for url in urls],\n    return_exceptions=True,\n)",
            "with contextlib.ExitStack() as stack:\n    files = [stack.enter_context(open(p)) for p in paths]\n    data = [f.read() for f in files]",
            "def memoize(fn):\n    cache: dict = {}\n    @functools.wraps(fn)\n    def wrapper(*args):\n        if args not in cache:\n            cache[args] = fn(*args)\n        return cache[args]\n    return wrapper",
            "matcher = re.compile(\n    r\"(?P<year>\\d{4})-(?P<month>\\d{2})-(?P<day>\\d{2})\"\n)\nif m := matcher.fullmatch(text):\n    year = int(m.group(\"year\"))",
            "T = TypeVar(\"T\")\n\ndef first(iterable: Iterable[T], default: T | None = None) -> T | None:\n    return next(iter(iterable), default)",
            "import tomllib\nwith open(\"pyproject.toml\", \"rb\") as fh:\n    cfg = tomllib.load(fh)\nversion = cfg[\"project\"][\"version\"]",
            "subprocess.run(\n    [\"ruff\", \"check\", \"--fix\", str(src)],\n    check=True,\n    capture_output=True,\n)",
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
    # When more prompts are requested than exist, cycle through full shuffled
    # passes instead of picking each one independently. This spreads repeats
    # out evenly rather than clustering the same prompt several times in a row.
    result: list[str] = []
    while len(result) < count:
        batch = list(source)
        rng.shuffle(batch)
        result.extend(batch)
    return result[:count]
