"""Word tonicity — port of ``Trat_fon::tonica()`` from ``trat_fon.cpp``.

Cotovia removes the prosodic stress mark from *atonic* words (articles,
prepositions, clitic pronouns, most conjunctions, relatives).  The decision is
made from the word's grammatical category in ``atono_ou_tonico_aberto_ou_
pechado_e_w_x()``, which the C binary calls in the main pipeline
(``cotovia.cpp``) before it builds the phonetic sentence.

pycotovia has no morphosyntactic disambiguator, so it uses the first category
listed for the word in Cotovia's own ``palabrasFuncion.txt`` table.  Words that
are absent from that table are content words and are always tonic.
"""

from .function_words import FUNCTION_WORDS

# ADVERBIO(c) == (c >= ADVE && c <= ADVE_DISTR)
ADVE, ADVE_DISTR = 80, 93
# adverbio(c) == (c >= ADVE && c <= LOC_ADVE_DUBI) — the macro tonica() uses
LOC_ADVE_DUBI = 107

# Categories for which tonica() returns 1.  Adverbs are handled by range.
TONIC_CATEGORIES = frozenset({
    0,                       # unset
    4,                       # CONTR_INDEF_ART_DET
    6,                       # CONTR_PREP_ART_INDET
    10, 11, 12, 13, 14, 15,  # INDEF family
    20, 21, 22, 23, 24, 25,  # DEMO family
    26, 28, 29, 31,          # CONTR_(PREP_)DEMO_INDEF (_PRON)
    35, 36, 37,              # POSE family
    40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53,  # NUME family
    60, 61,                  # PRON_PERS_TON, CONTR_PREP_PRON_PERS_TON
    171, 172,                # INTER, EXCLA
    173, 175, 176,           # NOME, NOME_PROPIO, ADXECTIVO
    178, 180, 181, 182,      # VERBO, INFINITIVO, XERUNDIO, PARTICIPIO
    183,                     # INTERX
    254,                     # CAT_NON_CLASIFICADA
})

# Categories for which e_sustantivo() returns 1, so the noun timbre rules run.
#
# The C lists only NUME_CARDI_PRON among the numerals, because its
# disambiguator decides which numerals are pronouns in context. pycotovia has
# no disambiguator and takes the first category the word is listed under, so
# it treats the whole NUME family as nouns. Measured against the binary that
# is the closer approximation: "cento", "oito", "catrocentos" and
# "novecentos" all come out open, as the binary has them.
SUSTANTIVO_CATEGORIES = frozenset({
    11, 12,   # INDEF_PRON, INDEF_DET
    40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53,  # NUME family
    173, 175, 176,  # NOME, NOME_PROPIO, ADXECTIVO
    254,      # unknown word: treated as a content word by pycotovia
})

# ``#ifdef _MODO_NORMAL`` override in atono_ou_tonico_aberto_ou_pechado_e_w_x().
ALWAYS_TONIC = frozenset({"durante", "incluso"})


def _is_adverb(category: int) -> bool:
    return ADVE <= category <= LOC_ADVE_DUBI


def category_of(word: str, lang: str = "gl") -> int:
    """Return the grammatical category pycotovia assumes for ``word``.

    Function words get their first listed category; anything else is treated
    as an unclassified content word (``CAT_NON_CLASIFICADA``).
    """
    cats = FUNCTION_WORDS.get(lang, {}).get(word.lower())
    return cats[0] if cats else 254


def is_tonic(word: str, lang: str = "gl", *, is_last: bool = False) -> bool:
    """Return True when the word keeps its prosodic stress mark.

    Args:
        word: Orthographic word, lowercased or not.
        lang: ``"gl"`` or ``"es"``.
        is_last: True when no further word follows in the sentence.  The C
            code forces ``tonicidade = 1`` for the last word of a sentence,
            skipping over trailing punctuation.
    """
    if is_last:
        return True
    w = word.lower()
    if w in ALWAYS_TONIC:
        return True
    category = category_of(w, lang)
    if _is_adverb(category):
        return True
    return category in TONIC_CATEGORIES


def is_sustantivo(word: str, lang: str = "gl") -> bool:
    """Return True when the noun timbre rules apply — port of ``e_sustantivo()``."""
    category = category_of(word, lang)
    if ADVE <= category <= ADVE_DISTR:
        return True
    return category in SUSTANTIVO_CATEGORIES
