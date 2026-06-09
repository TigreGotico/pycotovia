"""Prosodic stress assignment — port of acentuar_prosodicamente() from sil_acen.cpp."""

from .charset import (
    vocal, vocal_acentuada, consonante,
    to_minuscula, e_acentuada, o_acentuada, a_acentuada,
    i_acentuada, u_acentuada, ACENTO_A_BASE,
)

SEPARADOR_SILABAS = '-'


def assign_stress(syllabified: str, lang: str = "gl") -> str:
    """Place the prosodic stress marker ^ after the stressed vowel.

    Args:
        syllabified: Syllabified word (e.g. "ca-sa", "can-tar")
        lang: "gl" for Galician, "es" for Spanish

    Returns:
        Word with ^ inserted after the stressed vowel, e.g. "ca^-sa"
    """
    if not syllabified:
        return syllabified

    if '^' in syllabified:
        return syllabified

    # Find orthographic accents — the LAST one determines stress
    last_accent_pos = -1
    for j, ch in enumerate(syllabified):
        if vocal_acentuada(ch):
            last_accent_pos = j

    if last_accent_pos >= 0:
        result = []
        for j, ch in enumerate(syllabified):
            b = ord(ch)
            if b in ACENTO_A_BASE and j != last_accent_pos:
                result.append(ACENTO_A_BASE[b])
            else:
                result.append(ch)
        stress_char = result[last_accent_pos]
        base = ACENTO_A_BASE.get(ord(stress_char), stress_char)
        result[last_accent_pos] = base
        result.insert(last_accent_pos + 1, '^')
        return "".join(result)

    # No orthographic accent — apply default rules
    word = syllabified.replace('-', '')
    if not word:
        return syllabified

    last = word[-1]
    result_list = list(syllabified)

    if consonante(last):
        if last == 'n' or last == 'N':
            if '-' in syllabified:
                stress_pos = _grave(syllabified)
            else:
                stress_pos = _aguda(syllabified)
        elif last == 's' or last == 'S':
            if '-' not in syllabified:
                stress_pos = _aguda(syllabified)
            else:
                ppt = len(syllabified) - 1
                if ppt >= 2 and vocal(syllabified[ppt - 2]):
                    chk = syllabified[ppt - 1]
                    if chk == 'i' or chk == 'u':
                        stress_pos = _aguda(syllabified)
                    else:
                        stress_pos = _grave(syllabified)
                else:
                    stress_pos = _grave(syllabified)
        else:
            stress_pos = _aguda(syllabified)
    elif vocal(last):
        if last in ('i', 'I', 'u', 'U'):
            if len(word) > 1 and vocal(word[-2]):
                stress_pos = _aguda(syllabified)
            else:
                if '-' in syllabified:
                    stress_pos = _grave(syllabified)
                else:
                    stress_pos = _aguda(syllabified)
        else:
            if '-' in syllabified:
                stress_pos = _grave(syllabified)
            else:
                stress_pos = _aguda(syllabified)
    else:
        return syllabified

    if stress_pos is not None:
        result_list.insert(stress_pos + 1, '^')

    return "".join(result_list)


def _grave(s: str) -> int | None:
    """Find stressed vowel for grave (penultimate) words — port of grave() in sil_acen.cpp.

    Scans backwards from end to find last syllable separator, then finds
    the last vowel in the penultimate syllable.
    """
    # Scan backwards to find last syllable separator
    pos = len(s) - 1
    while pos >= 0 and s[pos] != SEPARADOR_SILABAS:
        pos -= 1

    # From there, scan backwards to find a vowel
    while pos >= 0 and not vocal(s[pos]):
        pos -= 1

    if pos < 0:
        return None

    # Apply i/u exception logic (mirroring C's grave())
    # NOTE: The C source has a precedence bug: `(*p-2)=='g'` is parsed as
    # `(*p)-2=='g'`, so for *p=='i' the guard is always true.  We keep the
    # correct logic here (check the character two positions back).  This means
    # words like "bui" will differ from the binary: py → buj, bin → bwi.
    b = ord(s[pos])
    if b in (0x69, 0x75, 0x49, 0x55, 0xFC, 0xDC):
        if pos > 0 and vocal(s[pos - 1]):
            # EXCEPT: silent u — if prev is u/ü preceded by q/g, don't shift
            prev = s[pos - 1]
            if prev == 'u' or ord(prev) == 0xFC:
                if pos >= 2 and s[pos - 2] in ('q', 'g'):
                    return pos  # Keep stress — silent u
            pos -= 1  # Shift stress back
    return pos


def _aguda(s: str) -> int | None:
    """Find stressed vowel for aguda (final) words — port of aguda() in sil_acen.cpp.

    Scans backwards from end to find the last vowel.
    """
    pos = len(s) - 1
    while pos >= 0 and not vocal(s[pos]):
        pos -= 1

    if pos < 0:
        return None

    # NOTE: Same as _grave() — the C source has a precedence bug in
    # `(*p-2)=='g'`.  We keep the correct logic (check s[pos-2]).
    b = ord(s[pos])
    if b in (0x69, 0x75, 0x49, 0x55, 0xFC, 0xDC):
        if pos > 0 and vocal(s[pos - 1]):
            # EXCEPT: silent u after q/g — don't shift back
            if not (s[pos - 1] == 'u' and pos >= 2 and s[pos - 2] in ('q', 'g')):
                pos -= 1
    return pos
