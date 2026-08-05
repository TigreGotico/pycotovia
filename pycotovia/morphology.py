"""Verb analysis — port of the verb path of `verbos.cpp`.

Given a surface word, this module answers the question the prosodic stage
needs: is this a verb form, and if so which verb, which conjugation model,
and which tense and person?

The binary needs the same answer for `manexo_do_timbre_verbal()`, which
decides whether a stressed `e` or `o` opens. Without it, verb forms fall
through to the noun rules and come out with the wrong timbre.

The algorithm follows `gbm_verbos::detectar_desinencias_verbais()` and
`gbm_verbos::comprobar_raiz_verbal()`:

1. Search the reversed ending dictionary for the longest ending the word can
   carry, then walk back through the shorter endings that share its first
   letter. `abades` finds `-abades` and also `-ades`.
2. Each ending carries a flat list of alternating tense and model codes.
3. Strip the ending. What is left is a candidate root. Look it up in the root
   dictionary, which is an exact-match binary search.
4. Keep the (tense, model) pairs whose model the root actually has. Those are
   the analyses.

Roots recorded as `0` in `verbos.txt` are the irregular verbs, whose forms
carry no separable stem. They are reached through a separate branch.

Both dictionaries are searched with the binary searches in `lookup.py`, and
`verb_data.py` keeps them in file order, because the order decides which
entries a binary search can reach.
"""

from typing import NamedTuple

from .charset import ACENTO_A_BASE
from .lookup import buscar_inicio, buscar_palabra
from .stress import assign_stress
from .syllabify import syllabify
from .verb_data import (DESINENCIAS, ENCLITICOS, EXCEPCIONS_VERBOS,
                        RAICES_VERBAIS, RAIZ_IRREGULAR)

#: Ending strings, in file order, for the binary search.
_DESINENCIA_KEYS = tuple(entry[0] for entry in DESINENCIAS)

#: Root strings, in file order, for the binary search.
_RAIZ_KEYS = tuple(entry[0] for entry in RAICES_VERBAIS)

#: Enclitic pronouns, reversed, in file order, for the binary search.
_ENCLITICO_KEYS = tuple(entry[0] for entry in ENCLITICOS)


class Desinencia(NamedTuple):
    """A candidate verb ending and the (tense, model) pairs it allows."""

    #: The ending, written forwards.
    desinencia: str
    #: Flat list of alternating tense and conjugation-model codes, as stored.
    codigos: tuple[int, ...]

    def pares(self):
        """Yield the (tense, model) pairs.

        The C walks `cod_desinencia` with two cursors, one starting at 0 for
        tenses and one at 1 for models, both stepping by two.
        """
        for i in range(0, len(self.codigos) - 1, 2):
            yield self.codigos[i], self.codigos[i + 1]


class AnaliseVerbal(NamedTuple):
    """One reading of a surface form as a verb."""

    #: The infinitive, as spelled in `verbos.txt`.
    infinitivo: str
    #: The root the ending was stripped back to. Empty for irregulars.
    raiz: str
    #: Conjugation model number, the key into the verb-timbre tables.
    modelo: int
    #: Tense and person code.
    tempo: int
    #: The ending that was stripped.
    desinencia: str
    #: The enclitic pronoun that was stripped first, or "".
    enclitico: str = ""


def detectar_desinencias_verbais(palabra: str) -> list[Desinencia]:
    """Find every ending the word could carry, longest first.

    Port of `detectar_desinencias_verbais()`. After it finds an ending, the C
    restricts the next search to the entries before it and looks again, which
    picks up shorter endings that share the first letter of the reversed form.
    """
    found: list[Desinencia] = []
    limite = len(_DESINENCIA_KEYS)

    while True:
        pos = buscar_inicio(_DESINENCIA_KEYS, palabra, inverso=True,
                            limite=limite)
        if pos < 0:
            return found

        rev_ending, codigos = DESINENCIAS[pos]
        found.append(Desinencia(rev_ending[::-1], codigos))

        # Are there shorter endings still? The C truncates the ending it just
        # found to the length of the entry before it, and keeps going only
        # while the two still start with the same letter.
        if pos == 0:
            return found
        previous = DESINENCIAS[pos - 1][0]
        if rev_ending[:len(previous)][:1] != previous[:1]:
            return found
        limite = pos


def _raiz_ten_modelo(pos_raiz: int, modelo: int):
    """Yield the infinitives at this root that carry the model."""
    for infinitivo, modelos in RAICES_VERBAIS[pos_raiz][1]:
        if not modelos:
            break
        for candidato in modelos:
            if candidato == modelo:
                yield infinitivo


def analizar_verbo(palabra: str) -> list[AnaliseVerbal]:
    """Return every reading of `palabra` as a verb form.

    Port of `comprobar_raiz_verbal()`. An empty list means the word is not a
    verb form this dictionary can account for.

    The readings come back in the order the C produces them: outer loop over
    endings, longest first; inner loop over the (tense, model) pairs of that
    ending; innermost over the infinitives listed at the root.
    """
    palabra = palabra.lower()
    # Words that look like verb forms but are not. Port of `excep_verbo()`.
    if buscar_palabra(EXCEPCIONS_VERBOS, palabra) >= 0:
        return []
    analises: list[AnaliseVerbal] = []
    for base, enclitico in eliminar_encliticos(palabra):
        analises.extend(_analizar_sen_encliticos(base, enclitico))
        if not analises and enclitico:
            sen_acento = quitar_acento_de_enclitico(base)
            if sen_acento:
                analises.extend(
                    _analizar_sen_encliticos(sen_acento, enclitico))
        if analises:
            break
    return analises


def _analizar_sen_encliticos(palabra: str, enclitico: str) -> list[AnaliseVerbal]:
    """The analysis proper, on a form with its enclitics already removed."""
    analises: list[AnaliseVerbal] = []

    for desinencia in detectar_desinencias_verbais(palabra):
        raiz = palabra[:len(palabra) - len(desinencia.desinencia)]

        if raiz:
            pos_raiz = buscar_palabra(_RAIZ_KEYS, raiz)
            if pos_raiz < 0:
                continue
            for tempo, modelo in desinencia.pares():
                for infinitivo in _raiz_ten_modelo(pos_raiz, modelo):
                    analises.append(AnaliseVerbal(
                        infinitivo, RAICES_VERBAIS[pos_raiz][0], modelo,
                        tempo, desinencia.desinencia, enclitico))
        else:
            # The whole word is the ending, so there is no separable stem.
            # The C scans the leading run of "0" roots, which are the
            # irregular verbs, for one that carries the model.
            for tempo, modelo in desinencia.pares():
                for pos, (clave, grupos) in enumerate(RAICES_VERBAIS):
                    if clave != RAIZ_IRREGULAR:
                        break
                    for infinitivo, modelos in grupos:
                        if modelo in modelos:
                            analises.append(AnaliseVerbal(
                                infinitivo, "", modelo, tempo,
                                desinencia.desinencia, enclitico))

    return analises


def quitar_acento_de_enclitico(raiz: str) -> str | None:
    """Undo the graphic accent that attaching an enclitic added.

    Galician writes an accent on the verb when an enclitic would otherwise
    move the stress: `accede` + `se` is spelled `accédese`. Once the enclitic
    is stripped, `accéde` is not a form the root dictionary knows; `accede`
    is.

    `reacentua()` decides this by re-deriving where the accent belongs and
    comparing. This does the same test with pycotovia's own stress module: if
    the default stress rules already land on the vowel that carries the
    accent, the accent was redundant and is removed. Returns the corrected
    form, or None when the accent is part of the spelling.
    """
    posicion = next((i for i, ch in enumerate(raiz)
                     if ord(ch) in ACENTO_A_BASE), -1)
    if posicion < 0:
        return None

    plano = "".join(ACENTO_A_BASE.get(ord(ch), ch) for ch in raiz)
    marcado = assign_stress(syllabify(plano))
    caret = marcado.find("^")
    if caret < 0:
        return None
    # Where the caret lands, counting only the letters.
    tonica = len(marcado[:caret].replace("-", "")) - 1
    return plano if tonica == posicion else None


def eliminar_encliticos(palabra: str) -> list[tuple[str, str]]:
    """Yield (stem, enclitic) for every enclitic the word could end with.

    Port of `eliminar_encliticos()`. The C finds the longest enclitic first,
    then steps backwards through the list while the reversed word still starts
    with the same letter, which produces the shorter enclitics nested inside
    it: `dállelo` offers `llelo`, then `lo`.

    The first pair is always `(palabra, "")`, the reading with no enclitic.
    """
    out = [(palabra, "")]
    pos = buscar_inicio(_ENCLITICO_KEYS, palabra, inverso=True)
    reversed_word = palabra[::-1]

    while pos >= 0:
        enclitico = _ENCLITICO_KEYS[pos][::-1]
        if not enclitico or len(enclitico) >= len(palabra):
            break
        out.append((palabra[:len(palabra) - len(enclitico)], enclitico))
        if pos == 0:
            break
        # Step back to the next shorter enclitic that still matches.
        previous = _ENCLITICO_KEYS[pos - 1]
        if reversed_word[:1] != previous[:1]:
            break
        pos -= 1
        while pos >= 0 and not reversed_word.startswith(_ENCLITICO_KEYS[pos]):
            if _ENCLITICO_KEYS[pos][:1] != reversed_word[:1]:
                pos = -1
                break
            pos -= 1

    return out


def e_verbo(palabra: str) -> bool:
    """Does the dictionary account for this word as a verb form?"""
    return bool(analizar_verbo(palabra))
