"""Syllabification — port of separar_silabas() from sil_acen.cpp.

Splits words into syllables with `-` separators using Galician/Spanish phonotactics.
"""

from .charset import (
    vocal, vocal_aberta, vocal_feble, consonante,
    es_diptongo, es_triptongo, GRUPOS_INDIVISIBLES,
    enne_minuscula, u_con_dierese, e_acentuada, o_acentuada,
)


def syllabify(word: str) -> str:
    """Split a word into syllables with `-` separators.

    Args:
        word: Input word (plain text, may have orthographic accents)

    Returns:
        Syllabified word, e.g. "ca-sa", "can-ta", "glo-ria"
    """
    if not word:
        return word

    result = []
    i = 0
    n = len(word)
    last_was_sep = False

    while i < n:
        ch = word[i]

        # Copy non-letters as-is
        if not (vocal(ch) or consonante(ch)):
            result.append(ch)
            last_was_sep = False
            i += 1
            continue

        # --- Consonant section ---
        if consonante(ch) or (ch in ('q', 'Q', 'g', 'G') and i + 1 < n
                              and word[i + 1] in (0x75, 0x55, 0xFC, 0xDC)):
            # Leading consonants at word start: all go to onset
            if i == 0:
                onset = []
                while i < n and (consonante(word[i]) or
                                 (word[i] in ('q', 'Q') and i + 1 < n and
                                  word[i + 1] in ('u', 'U', u_con_dierese))):
                    onset.append(word[i])
                    i += 1
                result.extend(onset)
                if i < n and not last_was_sep:
                    pass
                last_was_sep = False
                continue

            # Consonant clusters
            c1 = word[i]

            # Silent u: qu/gu before vowel
            if (ch in ('q', 'Q', 'g', 'G') and i + 1 < n
                    and word[i + 1] in ('u', 'U', u_con_dierese)
                    and i + 2 < n
                    and vocal(word[i + 2])
                    and word[i + 2] not in (e_acentuada, o_acentuada)):
                # qu/gu + vowel -> bound to onset, insert - before
                if not last_was_sep:
                    result.append('-')
                    last_was_sep = True
                result.append(ch)
                result.append(word[i + 1])
                i += 2
                last_was_sep = False
                continue

            # Read ahead to count consonants
            ci = i
            while ci < n and consonante(word[ci]):
                ci += 1
            cc = ci - i

            if cc == 0:
                i += 1
                continue

            # Trailing consonants: if only consonants remain, attach to current syllable
            rest_all_consonants = True
            for j in range(i, n):
                if not consonante(word[j]):
                    rest_all_consonants = False
                    break
            if rest_all_consonants:
                result.append(word[i:])
                i = n
                continue

            if cc == 1:
                # Single consonant → onset of next syllable
                if not last_was_sep:
                    result.append('-')
                    last_was_sep = True
                result.append(word[i])
                i += 1
                last_was_sep = False

            elif cc == 2:
                pair = (word[i] + word[i + 1]).lower()
                if pair in GRUPOS_INDIVISIBLES:
                    if not last_was_sep:
                        result.append('-')
                        last_was_sep = True
                    result.append(word[i])
                    result.append(word[i + 1])
                    i += 2
                else:
                    result.append(word[i])
                    if not last_was_sep:
                        result.append('-')
                        last_was_sep = True
                    result.append(word[i + 1])
                    i += 2
                last_was_sep = False

            elif cc == 3:
                pair2 = (word[i + 1] + word[i + 2]).lower()
                if pair2 in GRUPOS_INDIVISIBLES:
                    # C-CC
                    result.append(word[i])
                    if not last_was_sep:
                        result.append('-')
                        last_was_sep = True
                    result.append(word[i + 1])
                    result.append(word[i + 2])
                    i += 3
                else:
                    # CC-C
                    result.append(word[i])
                    result.append(word[i + 1])
                    if not last_was_sep:
                        result.append('-')
                        last_was_sep = True
                    result.append(word[i + 2])
                    i += 3
                last_was_sep = False

            else:  # cc >= 4
                # CC-CC
                result.append(word[i])
                result.append(word[i + 1])
                if not last_was_sep:
                    result.append('-')
                    last_was_sep = True
                result.append(word[i + 2])
                result.append(word[i + 3])
                i += cc
                last_was_sep = False

            continue

        # --- Vowel section ---
        if vocal(ch):
            vstart = i
            # Collect vowel sequence
            while i < n and vocal(word[i]):
                i += 1
            vseq = word[vstart:i]
            vlen = len(vseq)

            if vlen == 1:
                result.append(vseq)
                if not last_was_sep:
                    pass
                last_was_sep = False

            elif vlen == 2:
                if es_diptongo(vseq[0], vseq[1]):
                    result.append(vseq)
                else:
                    # Hiatus: V-V
                    result.append(vseq[0])
                    if not last_was_sep:
                        result.append('-')
                        last_was_sep = True
                    result.append(vseq[1])
                last_was_sep = False

            elif vlen == 3:
                if es_triptongo(vseq[0], vseq[1], vseq[2]):
                    result.append(vseq)
                else:
                    if es_diptongo(vseq[0], vseq[1]):
                        # VV-V
                        result.append(vseq[0])
                        result.append(vseq[1])
                        if not last_was_sep:
                            result.append('-')
                            last_was_sep = True
                        result.append(vseq[2])
                    else:
                        # V-VV
                        result.append(vseq[0])
                        if not last_was_sep:
                            result.append('-')
                            last_was_sep = True
                        result.append(vseq[1])
                        result.append(vseq[2])
                    last_was_sep = False

            else:
                # 4+ vowels in sequence — unlikely in Galician/Spanish
                # Simple rule: split into groups of 1-2
                j = 0
                while j < vlen:
                    if j > 0:
                        if not last_was_sep:
                            result.append('-')
                            last_was_sep = True
                    if j + 1 < vlen and es_diptongo(vseq[j], vseq[j + 1]):
                        result.append(vseq[j])
                        result.append(vseq[j + 1])
                        j += 2
                    else:
                        result.append(vseq[j])
                        j += 1
                    last_was_sep = False

    return "".join(result)
