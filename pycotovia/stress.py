"""Prosodic stress assignment — port of acentuar_prosodicamente() from sil_acen.cpp."""

from .charset import (
    vocal, vocal_acentuada, consonante,
    to_minuscula, e_acentuada, o_acentuada, a_acentuada,
    i_acentuada, u_acentuada, ACENTO_A_BASE,
)

SEPARADOR_SILABAS = '-'

# Port of diacriticos_oposicion_aberta_pechada[] in sil_acen.cpp.
#
# For these words the graphic accent marks an open/closed opposition rather
# than stress, so Cotovia keeps the accented vowel instead of replacing it
# with the base vowel plus a stress mark.  The rule engine then maps é/ó to
# the open phonemes E/O.  The entries are matched against the *syllabified*
# word, which is why some of them carry syllable separators.
#
# DELIBERATE DIVERGENCE — adjudicated upstream bug.
#
# The C loop is:
#
#     cont = 0;
#     while (*diacriticos_oposicion_aberta_pechada[cont++] != 0)
#        if (strcmp(diacriticos_oposicion_aberta_pechada[cont], pal_entrada) == 0)
#
# `cont++` is in the guard, so the guard tests entry N while the body compares
# entry N+1.  Entry 0 ("é") is therefore never compared, and the "\0"
# terminator is compared instead.  The binary emits closed `e^` for "é" at
# -t0..-t2 as a result.
#
# pycotovia keeps "é" in the list, which is what the table plainly intends.
# Documented in cotovia-mirror PR #4 (reference only — not to merge).
#
# The blast radius is confined to -t0..-t2: at -t3 the prosodic stage opens
# "é" to `E^` anyway, so the mode the Cotovia-alphabet voices were trained on
# is unaffected.  See docs/parity.md.
DIACRITICOS_OPOSICION = (
    "é",
    "ó", "ós", "có", "cós", "nós", "vós", "vén", "vés",
    "pré-sa", "bó-la", "bó-las", "ó-so", "cóm-pre", "pó-la",
    "tén", "té", "dó", "sé", "nó", "só",
)


def diacritico_dif_aberta_pechada(syllabified: str) -> str | None:
    """Return the stressed form of an open/closed-opposition word, else None.

    Port of ``diacritico_dif_aberta_pechada()`` in ``sil_acen.cpp``: the
    prosodic stress mark goes after the first é/ó and the accent is kept.
    """
    pos = -1
    for i, ch in enumerate(syllabified):
        if ch in ('é', 'ó'):
            pos = i
            break
    if pos < 0:
        return None
    if syllabified not in DIACRITICOS_OPOSICION:
        return None
    return syllabified[:pos + 1] + '^' + syllabified[pos + 1:]


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

    # Words whose graphic accent marks an open/closed opposition keep it.
    if lang == "gl":
        opos = diacritico_dif_aberta_pechada(syllabified)
        if opos is not None:
            return opos

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
    #
    # DELIBERATE DIVERGENCE — adjudicated upstream bug.  The C source has a
    # precedence bug: `(*p-2)=='g'` is parsed as `((*p)-2)=='g'`, so for
    # *p=='i' (0x69) the guard `(*p-2)=='g'` (0x67) is always true.  We keep
    # the correct logic here (check the character two positions back).
    # Documented in cotovia-mirror PR #2 (reference only — not to merge).
    # The upstream binary emits `bwi^`/`fwi^`/`kwi^Do`; pycotovia emits
    # `bu^j`/`fu^j`/`ku^jDo`.  Measured blast radius: 19 of 48024 words
    # (0.04%) on the 5000-sentence Galician Wikipedia corpus.
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

    # Same adjudicated divergence as _grave(): the C source has a precedence
    # bug in `(*p-2)=='g'`.  We keep the correct logic (check s[pos-2]).
    # See cotovia-mirror PR #2.
    b = ord(s[pos])
    if b in (0x69, 0x75, 0x49, 0x55, 0xFC, 0xDC):
        if pos > 0 and vocal(s[pos - 1]):
            # EXCEPT: silent u after q/g — don't shift back
            if not (s[pos - 1] == 'u' and pos >= 2 and s[pos - 2] in ('q', 'g')):
                pos -= 1
    return pos
