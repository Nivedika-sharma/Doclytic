import random


def _replace_chars(text: str) -> str:
    replacements = {
        "o": ["0"],
        "e": ["c"],
        "i": ["l", "1"],
        "m": ["rn"],
        "s": ["5"],
        "a": ["@"],
    }

    chars = list(text)
    for i, char in enumerate(chars):
        options = replacements.get(char.lower())
        if options and random.random() < 0.05:
            chars[i] = random.choice(options)
    return "".join(chars)


def _swap_chars(text: str) -> str:
    chars = list(text)
    for i in range(len(chars) - 1):
        if chars[i].isalpha() and chars[i + 1].isalpha() and random.random() < 0.03:
            chars[i], chars[i + 1] = chars[i + 1], chars[i]
    return "".join(chars)


def _remove_colons(text: str) -> str:
    chars = []
    for char in text:
        if char == ":" and random.random() < 0.6:
            continue
        chars.append(char)
    return "".join(chars)


def _add_line_breaks(text: str) -> str:
    chars = []
    for char in text:
        chars.append(char)
        if char == " " and random.random() < 0.04:
            chars.append("\n")
    return "".join(chars)


def _spacing_issues(text: str) -> str:
    if random.random() < 0.5:
        text = text.replace(" ", "  ")
    if random.random() < 0.25:
        text = text.replace(" ", "")
    return text


def add_ocr_noise(text: str, noise_probability: float = 0.6) -> str:
    if random.random() > noise_probability:
        return text

    text = _replace_chars(text)
    text = _swap_chars(text)

    if random.random() < 0.5:
        text = _remove_colons(text)
    if random.random() < 0.5:
        text = _add_line_breaks(text)

    text = _spacing_issues(text)
    return text
