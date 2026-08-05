"""Vowel timbre — port of asignar_timbre_a_sustantivos() from trat_fon.cpp.

Galician distinguishes open and closed /e/ and /o/. Cotovia marks the open
ones by writing é/ó into the syllabified, stressed word; the rule engine then
maps those to the phonemes E and O.

This runs as part of the prosodic stage (see :mod:`pycotovia.prosody`), so it
only ever sees words that kept their stress mark.

The word lists live in :mod:`pycotovia.timbre_data`, generated straight from
the C source.
"""

from .lookup import buscar_palabra, buscar_inicio
from .timbre_data import (
    AGUDAS_PALABRAS_ABERTAS, AGUDAS_TERMINACIONS_ABERTAS,
    GRAVES_PALABRAS_ABERTAS, GRAVES_PALABRAS_PECHADAS,
    GRAVES_TERMINACIONS_ABERTAS, GRAVES_TERMINACIONS_PECHADAS,
    ESDR_TERMINACIONS_PECHADAS, ESDR_PALABRAS_PECHADAS,
)

VOC_ABERTA = True
VOC_PECHADA = False


def _singular(word: str) -> str:
    """Drop a trailing -s: the lists hold singulars."""
    return word[:-1] if word.endswith('s') else word


def _matches_reversed(word: str, entries: tuple[str, ...]) -> bool:
    """Suffix match against a reversed-entry list (EN_DICCIONARIO_INVERSO).

    Uses Cotovia's own binary search, not a linear scan: several of these
    lists are not fully sorted, and the entries the search cannot reach are
    entries the binary never matches either.
    """
    return buscar_inicio(entries, word, inverso=True) >= 0


def _in_list(word: str, entries: tuple[str, ...]) -> bool:
    return buscar_palabra(entries, word) >= 0


def posicion_acento(pal: str) -> int:
    """Return which syllable from the end carries the stress mark.

    1 = last (aguda), 2 = second to last (grave), 3 = third (esdrúxula);
    0 when there is no stress mark.
    """
    orde = 1
    for ch in reversed(pal):
        if ch == '^':
            return orde
        if ch == '-':
            orde += 1
    return 0


def estan_en_contacto_con_nasal(pal_sil_ac: str) -> bool:
    """True when the stressed vowel of a paroxytone touches a nasal.

    Walks back to the last syllable separator and looks for m/n/ñ on either
    side of it, with a stressed e/o/é/ó immediately before.
    """
    idx = pal_sil_ac.rfind('-')
    if idx <= 0:
        return False

    def at(i: int) -> str:
        return pal_sil_ac[i] if 0 <= i < len(pal_sil_ac) else '\0'

    if at(idx - 1) in ('m', 'n', 'ñ'):
        return at(idx - 2) == '^' and at(idx - 3) in ('é', 'ó', 'e', 'o')
    if at(idx + 1) in ('n', 'ñ'):
        # n and ñ can also be syllable-initial
        return at(idx - 1) == '^' and at(idx - 2) in ('é', 'ó', 'e', 'o')
    return False


def hai_grupo_eu_ou_na_antepenultima_silaba(pal: str) -> bool:
    """Always False — replicates a precedence bug in the C.

    The C writes ``while (pal != origen_palabra && !n_sil == 3)``, which
    parses as ``(!n_sil) == 3``. ``!n_sil`` is 0 or 1, so the test is never
    true and the loop always runs back to the start of the word. The
    "antepenultimate syllable" it then extracts is a single character, and
    ``strstr`` for "e^u"/"o^u" can never match it.

    The binary's real output is the specification here — the ProxectoNos
    voices were trained on it — so the guard stays dead rather than being
    silently "corrected" into a behaviour change.
    """
    return False


def timbre_en_agudas(palabra: str) -> bool:
    if _in_list(palabra, AGUDAS_PALABRAS_ABERTAS):
        return VOC_ABERTA
    if _matches_reversed(_singular(palabra), AGUDAS_TERMINACIONS_ABERTAS):
        return VOC_ABERTA
    return VOC_PECHADA


def timbre_en_graves(pal: str, pal_sil_ac: str) -> bool:
    singular = _singular(pal)
    if _in_list(singular, GRAVES_PALABRAS_ABERTAS):
        return VOC_ABERTA
    if _in_list(singular, GRAVES_PALABRAS_PECHADAS):
        return VOC_PECHADA
    if _matches_reversed(singular, GRAVES_TERMINACIONS_ABERTAS):
        return VOC_ABERTA
    if estan_en_contacto_con_nasal(pal_sil_ac):
        return VOC_PECHADA
    if _matches_reversed(singular, GRAVES_TERMINACIONS_PECHADAS):
        return VOC_PECHADA
    return VOC_ABERTA


def timbre_en_esdruxulas(palabra: str, pal_acentuada: str) -> bool:
    pal = _singular(palabra)
    if hai_grupo_eu_ou_na_antepenultima_silaba(pal_acentuada):
        return VOC_PECHADA
    if _matches_reversed(pal, ESDR_TERMINACIONS_PECHADAS):
        return VOC_PECHADA
    if _in_list(pal, ESDR_PALABRAS_PECHADAS):
        return VOC_PECHADA
    return VOC_ABERTA


def cambiar_por_timbre_aberto(palabra: str) -> str:
    """Open the stressed vowel: e becomes é, o becomes ó."""
    idx = palabra.find('^')
    if idx < 1:
        return palabra
    vowel = palabra[idx - 1]
    if vowel == 'e':
        return palabra[:idx - 1] + 'é' + palabra[idx:]
    if vowel == 'o':
        return palabra[:idx - 1] + 'ó' + palabra[idx:]
    return palabra


def asignar_timbre_a_sustantivos(palabra: str, palabra_acentuada: str) -> str:
    """Assign open or closed timbre to the stressed e/o of a noun.

    Args:
        palabra: the plain orthographic word, which drives the list lookups
        palabra_acentuada: the syllabified, stressed form to rewrite

    Returns:
        ``palabra_acentuada``, with the stressed vowel opened where the rules
        call for it.
    """
    # No stressed e or o: the open/closed opposition is neutralised.
    if "e^" not in palabra_acentuada and "o^" not in palabra_acentuada:
        return palabra_acentuada

    # Already carrying é/ó: an open diacritic word, nothing left to decide.
    if 'é' in palabra_acentuada or 'ó' in palabra_acentuada:
        return palabra_acentuada

    # A stressed falling diphthong is always closed.
    if "e^i" in palabra_acentuada or "o^u" in palabra_acentuada:
        return palabra_acentuada

    lugar = posicion_acento(palabra_acentuada)
    if lugar == 1:
        aberto = timbre_en_agudas(palabra)
    elif lugar == 2:
        aberto = timbre_en_graves(palabra, palabra_acentuada)
    elif lugar == 3:
        aberto = timbre_en_esdruxulas(palabra, palabra_acentuada)
    else:
        return palabra_acentuada

    if aberto:
        return cambiar_por_timbre_aberto(palabra_acentuada)
    return palabra_acentuada
