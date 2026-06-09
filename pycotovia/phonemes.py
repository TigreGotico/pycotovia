"""Phoneme inventory — port of fonemas.cpp."""

PHONEME_NAMES = [
    "#", "B", "D", "E", "G", "J", "N", "O", "S", "T",
    "Z", "a", "b", "d", "e", "f", "g", "i", "k", "l",
    "m", "n", "o", "p", "r", "s", "t", "u", "x", "tS",
    "rr", "j", "w", "L", "c", "ts", "s`", "gj", "jj", "ts`",
]

DOUBLE_PHONEME = {'tS': 29, 'rr': 30}

VOWEL_PHONEMES = {'a', 'e', 'E', 'i', 'o', 'O', 'u'}
SILENCE_VOICELESS_PLOSIVE = {'#', 't', 'k', 'p'}
SEGMENT_BOUNDARY = {'#', 't', 'k', 'p', 'f', 's', 'S', 'T', 'h'}
VOICELESS = {'#', 'p', 't', 'k', 'f', 's', 'S', 'T', 'x'}


def is_vowel(p: str) -> bool:
    return p[0:1] in VOWEL_PHONEMES


def is_voiceless(p: str) -> bool:
    return p[0:1] in VOICELESS


COTOVIA2IPA = {
    "#": "pau",
    "B": "β",
    "D": "ð",
    "E": "ɛ",
    "G": "ɣ",
    "J": "ɲ",
    "N": "ŋ",
    "O": "ɔ",
    "S": "ʃ",
    "T": "θ",
    "Z": "ʎ",
    "a": "a",
    "b": "b",
    "d": "d",
    "e": "e",
    "f": "f",
    "g": "ɡ",
    "i": "i",
    "k": "k",
    "l": "l",
    "m": "m",
    "n": "n",
    "o": "o",
    "p": "p",
    "r": "ɾ",
    "s": "s",
    "t": "t",
    "u": "u",
    "x": "x",
    "tS": "tʃ",
    "rr": "r",
    "j": "j",
    "w": "w",
    "L": "ʎ",
    "jj": "ʎ",
    "X": "x",
}


def cotovia_to_ipa(phoneme_str: str) -> str:
    result = []
    i = 0
    s = phoneme_str.strip()
    while i < len(s):
        if s[i] == ' ':
            result.append(' ')
            i += 1
            continue
        if i + 1 < len(s) and s[i:i + 2] in DOUBLE_PHONEME:
            result.append(COTOVIA2IPA.get(s[i:i + 2], s[i:i + 2]))
            i += 2
        else:
            result.append(COTOVIA2IPA.get(s[i], s[i]))
            i += 1
    return "".join(result)
