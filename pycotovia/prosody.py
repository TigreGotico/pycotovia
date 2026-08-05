"""Sentence-level prosody — port of the stage the binary runs before it
builds the phonetic sentence.

``Trat_fon::atono_ou_tonico_aberto_ou_pechado_e_w_x()`` is called from the
main pipeline at ``cotovia.cpp:2911``. For each word of the sentence it:

1. opens the stressed vowel of a verb form that carries a verbal timbre
   (``manexo_do_timbre_verbal``) — not ported, see below;
2. decides whether the word is tonic, and strips the ``^`` mark if it is not
   (``trat_fonetico``);
3. assigns open/closed vowel timbre to words that behave as nouns
   (``asignar_timbre_a_sustantivos``).

The effect shows up only in the binary's ``-t3`` output, which is what the
ProxectoNos Cotovia-alphabet gold transcriptions were produced from.

Not ported: ``manexo_do_timbre_verbal``. It resolves the timbre of a verb
form from the conjugation tables in ``verbos.txt``, which pycotovia does not
carry. Verb forms therefore fall through to the noun rules.
"""

from .charset import to_minusculas
from .timbre import asignar_timbre_a_sustantivos
from .tonicity import is_tonic, is_sustantivo


def apply_prosody(words: list[str], syllabified: list[str],
                  lang: str = "gl") -> list[str]:
    """Run the prosodic stage over one sentence.

    Args:
        words: the plain orthographic words of the sentence
        syllabified: the matching syllabified and stressed forms
        lang: ``"gl"`` or ``"es"``

    Returns:
        The syllabified forms, destressed and timbre-marked in place.
    """
    out = []
    last = len(words) - 1
    for idx, (word, form) in enumerate(zip(words, syllabified)):
        plain = to_minusculas(word)

        # The C forces tonicidade = 1 for the last word of the sentence.
        if is_tonic(plain, lang, is_last=(idx == last)):
            # trat_fonetico() strips the stress mark before it calls the
            # timbre rules, so an atonic word can never carry an open vowel.
            if lang == "gl" and is_sustantivo(plain, lang):
                form = asignar_timbre_a_sustantivos(plain, form)
        else:
            form = form.replace('^', '', 1)
        out.append(form)
    return out
