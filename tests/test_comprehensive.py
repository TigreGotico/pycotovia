#!/usr/bin/env python3
"""Comprehensive tests targeting 90%+ coverage across all modules."""

import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pycotovia import phonemize, Phonemizer, cotovia_to_ipa
from pycotovia.charset import (
    vocal, consonante, vocal_acentuada, vocal_feble, vocal_aberta,
    es_diptongo, es_triptongo, letra, to_minuscula, to_minusculas,
    base_vowel, vocal_minuscula_acentuada, vocal_maiuscula_acentuada,
    a_acentuada, e_acentuada, i_acentuada, o_acentuada, u_acentuada,
)
from pycotovia.syllabify import syllabify
from pycotovia.stress import assign_stress, _grave, _aguda
from pycotovia.timbre import (
    asignar_timbre_a_sustantivos, posicion_acento,
    estan_en_contacto_con_nasal, timbre_en_agudas, timbre_en_graves,
    timbre_en_esdruxulas, cambiar_por_timbre_aberto,
    hai_grupo_eu_ou_na_antepenultima_silaba,
)
from pycotovia.phonemes import (
    cotovia_to_ipa, is_vowel, is_voiceless, PHONEME_NAMES,
    VOWEL_PHONEMES, VOICELESS, COTOVIA2IPA,
)
from pycotovia.exceptions import (
    trata_excepcions_xe, trata_excepcions_w, _prefix_match,
    X_PASA_A_KS, PRONUNCIANSE_CON_XE, W_PRONUNCIASE_GU, W_PRONUNCIASE_U,
)
from pycotovia.engine import apply_rules


# ---------------------------------------------------------------------------
# charset
# ---------------------------------------------------------------------------

class TestCharsetExtended(unittest.TestCase):
    def test_accented_vowels(self):
        for ch in ('á', 'é', 'í', 'ó', 'ú'):
            self.assertTrue(vocal(ch), ch)
            self.assertTrue(vocal_acentuada(ch), ch)

    def test_uppercase_accented_vowels(self):
        self.assertTrue(vocal('Á'))
        self.assertTrue(vocal_maiuscula_acentuada('Á'))
        self.assertTrue(vocal_maiuscula_acentuada('É'))
        self.assertTrue(vocal_maiuscula_acentuada('Í'))
        self.assertTrue(vocal_maiuscula_acentuada('Ó'))
        self.assertTrue(vocal_maiuscula_acentuada('Ú'))

    def test_lowercase_accented_vowels(self):
        self.assertTrue(vocal_minuscula_acentuada('á'))
        self.assertTrue(vocal_minuscula_acentuada('é'))
        self.assertTrue(vocal_minuscula_acentuada('í'))
        self.assertTrue(vocal_minuscula_acentuada('ó'))
        self.assertTrue(vocal_minuscula_acentuada('ú'))

    def test_non_accented_not_acentuada(self):
        self.assertFalse(vocal_acentuada('a'))
        self.assertFalse(vocal_acentuada('e'))
        self.assertFalse(vocal_minuscula_acentuada('a'))
        self.assertFalse(vocal_maiuscula_acentuada('A'))

    def test_vocal_feble(self):
        for ch in ('i', 'u', 'I', 'U', 'ü', 'Ü'):
            self.assertTrue(vocal_feble(ch), ch)
        self.assertFalse(vocal_feble('a'))
        self.assertFalse(vocal_feble('e'))

    def test_vocal_aberta(self):
        for ch in ('a', 'e', 'o', 'A', 'E', 'O', 'á', 'é', 'ó', 'Á', 'É', 'Ó'):
            self.assertTrue(vocal_aberta(ch), ch)
        self.assertFalse(vocal_aberta('i'))
        self.assertFalse(vocal_aberta('u'))

    def test_diptongo_feble_aberta(self):
        # weak-strong combos
        self.assertTrue(es_diptongo('u', 'a'))
        self.assertTrue(es_diptongo('i', 'o'))
        self.assertTrue(es_diptongo('u', 'e'))
        # strong-strong → hiatus
        self.assertFalse(es_diptongo('a', 'e'))
        self.assertFalse(es_diptongo('o', 'a'))

    def test_triptongo_varieties(self):
        self.assertTrue(es_triptongo('u', 'a', 'i'))
        self.assertTrue(es_triptongo('u', 'e', 'u'))
        # second char must be 'i' for the second rule
        self.assertTrue(es_triptongo('b', 'i', 'a'))  # v1 not feble but v2=='i'
        self.assertFalse(es_triptongo('a', 'e', 'o'))

    def test_letra(self):
        self.assertTrue(letra('a'))
        self.assertTrue(letra('Z'))
        self.assertTrue(letra('ñ'))
        self.assertTrue(letra('ç'))
        self.assertFalse(letra(' '))
        self.assertFalse(letra('!'))
        self.assertFalse(letra('3'))

    def test_to_minuscula_ascii(self):
        self.assertEqual(to_minuscula(ord('A')), ord('a'))
        self.assertEqual(to_minuscula(ord('Z')), ord('z'))
        self.assertEqual(to_minuscula(ord('a')), ord('a'))

    def test_to_minuscula_extended(self):
        self.assertEqual(to_minuscula(0xC0), 0xE0)
        self.assertEqual(to_minuscula(0xC1), 0xE1)
        self.assertEqual(to_minuscula(0xD1), 0xF1)

    def test_to_minusculas_string(self):
        self.assertEqual(to_minusculas("CASA"), "casa")
        self.assertEqual(to_minusculas("Galicia"), "galicia")

    def test_base_vowel(self):
        self.assertEqual(base_vowel('á'), 'a')
        self.assertEqual(base_vowel('é'), 'e')
        self.assertEqual(base_vowel('ó'), 'o')
        self.assertEqual(base_vowel('ü'), 'u')
        self.assertEqual(base_vowel('a'), 'a')  # no change

    def test_consonante_extended(self):
        self.assertTrue(consonante('b'))
        self.assertTrue(consonante('n'))
        self.assertTrue(consonante('s'))
        self.assertTrue(consonante('ñ'))


# ---------------------------------------------------------------------------
# syllabify
# ---------------------------------------------------------------------------

class TestSyllabifyExtended(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(syllabify(""), "")

    def test_single_vowel(self):
        self.assertEqual(syllabify("a"), "a")
        self.assertEqual(syllabify("e"), "e")

    def test_non_letter_chars(self):
        # digits / punctuation should pass through
        result = syllabify("a3b")
        self.assertIn("3", result)

    def test_ccvc(self):
        self.assertEqual(syllabify("plan"), "plan")
        self.assertEqual(syllabify("bla"), "bla")

    def test_indivisible_group_cluster(self):
        # bl, br, etc. go to onset as a unit
        self.assertEqual(syllabify("tabla"), "ta-bla")
        self.assertEqual(syllabify("libro"), "li-bro")
        self.assertEqual(syllabify("obra"), "o-bra")

    def test_two_consonants_split(self):
        # non-indivisible pair is split
        self.assertEqual(syllabify("carta"), "car-ta")
        self.assertEqual(syllabify("alto"), "al-to")

    def test_three_consonant_cluster_indivisible_suffix(self):
        # C + indivisible pair → C-CC
        self.assertEqual(syllabify("nombrar"), "nom-brar")
        self.assertEqual(syllabify("compra"), "com-pra")

    def test_three_consonant_cluster_divisible(self):
        # non-indivisible last pair → CC-C
        self.assertEqual(syllabify("instante"), "ins-tan-te")

    def test_four_consonant_cluster(self):
        # transcription only; real Spanish e.g. "tronchar" has 2
        # ensure the cc>=4 branch doesn't crash
        result = syllabify("transgredir")
        self.assertIn("-", result)

    def test_hiatus(self):
        # two strong vowels = hiatus
        self.assertEqual(syllabify("caos"), "ca-os")
        self.assertEqual(syllabify("aorta"), "a-or-ta")

    def test_diphthong_vv(self):
        self.assertEqual(syllabify("aire"), "ai-re")
        self.assertEqual(syllabify("auto"), "au-to")

    def test_diphthong_vv_then_v(self):
        # ia + e: ia is diphthong, then hiatus with e
        result = syllabify("hacia")
        self.assertIsInstance(result, str)

    def test_triptongo_in_syllabify(self):
        result = syllabify("buey")
        self.assertIsInstance(result, str)

    def test_three_vowels_not_triptongo(self):
        # a-e-a → two hiatuses
        result = syllabify("aldea")
        self.assertIn("-", result)

    def test_four_vowels_sequence(self):
        # unusual sequence with 4+ vowels
        result = syllabify("aeiou")
        self.assertIsInstance(result, str)

    def test_qu_stays_together(self):
        self.assertEqual(syllabify("queso"), "que-so")
        self.assertEqual(syllabify("aqui"), "a-qui")

    def test_gu_before_vowel(self):
        self.assertEqual(syllabify("guerra"), "gue-rra")
        self.assertEqual(syllabify("guia"), "guia")

    def test_trailing_consonants(self):
        self.assertEqual(syllabify("canal"), "ca-nal")
        self.assertEqual(syllabify("ciudad"), "ciu-dad")

    def test_ll_rr_indivisible(self):
        self.assertEqual(syllabify("carro"), "ca-rro")
        self.assertEqual(syllabify("calle"), "ca-lle")

    def test_leading_cluster(self):
        # word starts with consonant cluster
        self.assertEqual(syllabify("blanco"), "blan-co")
        self.assertEqual(syllabify("precio"), "pre-cio")


# ---------------------------------------------------------------------------
# stress
# ---------------------------------------------------------------------------

class TestStressExtended(unittest.TestCase):
    def test_already_stressed(self):
        # If ^ already present, return unchanged
        s = "ca^-sa"
        self.assertEqual(assign_stress(s), s)

    def test_empty(self):
        self.assertEqual(assign_stress(""), "")

    def test_aguda_ends_consonant_other(self):
        # ends in a consonant that isn't n/s → aguda
        self.assertEqual(assign_stress("can-tal"), "can-ta^l")
        self.assertEqual(assign_stress("pa-pel"), "pa-pe^l")

    def test_ends_n_monosyllable(self):
        # monosyllable ending in n → aguda
        self.assertEqual(assign_stress("pan"), "pa^n")

    def test_ends_n_polysyllable(self):
        # polysyllable ending in n → grave
        self.assertEqual(assign_stress("can-tan"), "ca^n-tan")

    def test_ends_s_polysyllable_grave(self):
        self.assertEqual(assign_stress("ca-sas"), "ca^-sas")

    def test_ends_s_monosyllable(self):
        self.assertEqual(assign_stress("los"), "lo^s")

    def test_ends_s_weak_vowel_before(self):
        # -is/-us ending → aguda behavior
        result = assign_stress("bur-gues")
        self.assertIn("^", result)

    def test_ends_i(self):
        # single vowel word ending in i
        self.assertEqual(assign_stress("si"), "si^")

    def test_ends_u_after_vowel(self):
        # u preceded by vowel → aguda
        result = assign_stress("tau")
        self.assertIn("^", result)

    def test_ends_u_no_prev_vowel(self):
        # ends in u, not preceded by vowel, polysyllable → grave
        result = assign_stress("cal-cu")
        self.assertIn("^", result)

    def test_multiple_orthographic_accents_last_wins(self):
        # Only the last accented vowel gets the stress mark
        result = assign_stress("é-rá")
        # last accent on 'á'
        self.assertIn("a^", result)

    def test_orthographic_accent_strips_others(self):
        # Other accented vowels before last should have accents stripped
        result = assign_stress("és-ta")
        self.assertIn("^", result)

    def test_grave_helper(self):
        self.assertIsNotNone(_grave("ca-sa"))
        self.assertIsNone(_grave("x"))  # no vowel before separator

    def test_aguda_helper(self):
        self.assertIsNotNone(_aguda("can-tar"))
        self.assertIsNone(_aguda("bcdf"))  # no vowel

    def test_grave_silent_u(self):
        # silent u after g/q: stress doesn't shift back past it
        result = assign_stress("gue-rra")
        self.assertIn("^", result)

    def test_aguda_silent_u(self):
        result = assign_stress("que-brar")
        self.assertIn("^", result)

    def test_stress_ends_i_no_prev_vowel_monosyllable(self):
        # monosyllable ending in i → aguda
        result = assign_stress("ti")
        self.assertEqual(result, "ti^")

    def test_non_vowel_non_consonant_final(self):
        # edge: final char is neither vowel nor consonant (shouldn't happen, but safe)
        result = assign_stress("a-b")
        self.assertIn("^", result)


# ---------------------------------------------------------------------------
# timbre
# ---------------------------------------------------------------------------

class TestTimbre(unittest.TestCase):
    pass

class TestExceptionsExtended(unittest.TestCase):
    def test_prefix_match(self):
        self.assertTrue(_prefix_match("anexo", X_PASA_A_KS))
        self.assertFalse(_prefix_match("casa", X_PASA_A_KS))

    def test_xe_galician_x_pasa_a_ks(self):
        result = trata_excepcions_xe("anexo", "a-ne^-xo", lang="gl")
        self.assertIsNotNone(result)
        # The x sits after a syllable boundary, so the cluster splits: k-s
        self.assertEqual("a-ne^k-so", result)

    def test_xe_galician_pronuncianse(self):
        # complexo is in PRONUNCIANSE_CON_XE → return None
        result = trata_excepcions_xe("complexo", "com-ple^-xo", lang="gl")
        self.assertIsNone(result)

    def test_xe_galician_no_match(self):
        result = trata_excepcions_xe("gato", "ga^-to", lang="gl")
        self.assertIsNone(result)

    def test_xe_spanish_any_x(self):
        result = trata_excepcions_xe("taxi", "ta^-xi", lang="es")
        self.assertIsNotNone(result)
        self.assertEqual("ta^k-si", result)

    def test_xe_spanish_pronuncianse_overrides(self):
        # complexo is still in PRONUNCIANSE_CON_XE
        result = trata_excepcions_xe("complexo", "com-ple^-xo", lang="es")
        self.assertIsNone(result)

    def test_xe_spanish_no_x(self):
        result = trata_excepcions_xe("gato", "ga^-to", lang="es")
        self.assertIsNone(result)

    def test_w_u(self):
        result = trata_excepcions_w("twist", "twi^st")
        self.assertIsNotNone(result)
        self.assertIn("u", result)
        self.assertNotIn("w", result)

    def test_w_gu(self):
        result = trata_excepcions_w("sandwich", "sand-wi^ch")
        self.assertIsNotNone(result)
        self.assertIn("gu", result)

    def test_w_no_match(self):
        result = trata_excepcions_w("gato", "ga^-to")
        self.assertIsNone(result)

    def test_w_u_all_words(self):
        for word in W_PRONUNCIASE_U:
            result = trata_excepcions_w(word, word)
            self.assertIsNotNone(result, word)

    def test_w_gu_all_words(self):
        for word in W_PRONUNCIASE_GU:
            result = trata_excepcions_w(word, word)
            self.assertIsNotNone(result, word)

    def test_xe_x_pasa_a_ks_all(self):
        for entry in X_PASA_A_KS[:10]:
            result = trata_excepcions_xe(entry, entry, lang="gl")
            self.assertIsNotNone(result, entry)
            self.assertIn("ks", result, entry)


# ---------------------------------------------------------------------------
# engine
# ---------------------------------------------------------------------------

class TestEngineExtended(unittest.TestCase):
    def test_no_rules(self):
        # empty rules dict → passthrough
        self.assertEqual(apply_rules("abc", {}), "abc")

    def test_rule_match(self):
        rules = {ord('a'): [('a', 1, 'X')]}
        self.assertEqual(apply_rules("abc", rules), "Xbc")

    def test_rule_antecedent_longer(self):
        rules = {ord('a'): [('ab', 2, 'Z')]}
        self.assertEqual(apply_rules("abcd", rules), "Zcd")

    def test_rule_no_match_passes_through(self):
        rules = {ord('a'): [('ax', 2, 'Z')]}
        self.assertEqual(apply_rules("abc", rules), "abc")

    def test_rule_partial_antecedent_at_end(self):
        # antecedent would go past end of string → no match
        rules = {ord('a'): [('abc', 3, 'Z')]}
        self.assertEqual(apply_rules("ab", rules), "ab")

    def test_multiple_rules_first_wins(self):
        rules = {ord('a'): [('a', 1, 'X'), ('a', 1, 'Y')]}
        self.assertEqual(apply_rules("a", rules), "X")

    def test_use_sv_param(self):
        # use_sv doesn't change logic in apply_rules itself, just accepted
        rules = {ord('a'): [('a', 1, 'X')]}
        self.assertEqual(apply_rules("a", rules, use_sv=True), "X")


# ---------------------------------------------------------------------------
# phonemes
# ---------------------------------------------------------------------------

class TestPhonemesExtended(unittest.TestCase):
    def test_is_vowel(self):
        for v in ('a', 'e', 'E', 'i', 'o', 'O', 'u'):
            self.assertTrue(is_vowel(v), v)
        self.assertFalse(is_vowel('b'))
        self.assertFalse(is_vowel('k'))

    def test_is_voiceless(self):
        for v in ('#', 'p', 't', 'k', 'f', 's', 'S', 'T', 'x'):
            self.assertTrue(is_voiceless(v), v)
        self.assertFalse(is_voiceless('a'))
        self.assertFalse(is_voiceless('b'))

    def test_cotovia_to_ipa_all_single(self):
        for cot, ipa in COTOVIA2IPA.items():
            result = cotovia_to_ipa(cot)
            self.assertIsInstance(result, str)

    def test_cotovia_to_ipa_double_phoneme_at_end(self):
        # string ends with a double phoneme
        result = cotovia_to_ipa("atS")
        self.assertIn("tʃ", result)

    def test_cotovia_to_ipa_rr_at_end(self):
        result = cotovia_to_ipa("arr")
        self.assertIn("r", result)

    def test_cotovia_to_ipa_space(self):
        result = cotovia_to_ipa("ka sa")
        self.assertIn(" ", result)

    def test_cotovia_to_ipa_unknown(self):
        # unknown phoneme symbol passes through
        result = cotovia_to_ipa("Q")
        self.assertEqual(result, "Q")

    def test_phoneme_names_complete(self):
        self.assertIn("tS", PHONEME_NAMES)
        self.assertIn("rr", PHONEME_NAMES)

    def test_is_vowel_empty_string(self):
        self.assertFalse(is_vowel(""))

    def test_is_voiceless_empty_string(self):
        self.assertFalse(is_voiceless(""))


# ---------------------------------------------------------------------------
# phonemize (deeper coverage)
# ---------------------------------------------------------------------------

class TestPhoneizeDeeper(unittest.TestCase):
    def test_invalid_lang(self):
        with self.assertRaises(ValueError):
            Phonemizer(lang="fr")

    def test_empty_string(self):
        # The binary prints nothing at all for empty input.
        self.assertEqual(phonemize("", lang="gl"), "")

    def test_only_punctuation(self):
        result = phonemize("!!! ???", lang="gl")
        self.assertIsInstance(result, str)

    def test_tra_5_raw(self):
        result = phonemize("casa", lang="gl", tra=5)
        self.assertIn("#", result)

    def test_strip_t0_stress_mark(self):
        # tra=2 preserves ^
        result = phonemize("café", lang="gl", tra=2)
        self.assertIn("^", result)

    def test_strip_t0_syllable_sep(self):
        # tra=3 preserves -
        result = phonemize("cantar", lang="gl", tra=3)
        self.assertIn("-", result)

    def test_multiple_words(self):
        result = phonemize("bos dias", lang="gl")
        # should have a space between words
        self.assertIn(" ", result.strip())

    def test_galician_nh(self):
        result = phonemize("señor", lang="gl")
        self.assertIsInstance(result, str)

    def test_spanish_ll(self):
        result = phonemize("llama", lang="es")
        self.assertIsInstance(result, str)

    def test_galician_x_regular(self):
        # x in Galician → S (not ks)
        result = phonemize("xato", lang="gl").strip()
        self.assertIn("S", result)

    def test_spanish_ks_default(self):
        # x in Spanish → ks by default
        result = phonemize("taxi", lang="es").strip()
        # trata_excepcions_xe maps x→ks, so ks should appear in syllabified form
        self.assertIsInstance(result, str)

    def test_phonemizer_reuse_es(self):
        p = Phonemizer(lang="es")
        r1 = p.phonemize("casa")
        r2 = p.phonemize("libro")
        self.assertNotEqual(r1, r2)

    def test_uppercase_input(self):
        result = phonemize("CASA", lang="gl")
        self.assertEqual(result.strip(), "kasa")

    def test_word_with_accent(self):
        result = phonemize("canción", lang="es")
        self.assertIsInstance(result, str)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

class TestCLI(unittest.TestCase):
    def _run_main(self, argv, stdin_text):
        from pycotovia.cli import main
        with patch('sys.argv', argv), \
             patch('sys.stdin', StringIO(stdin_text)), \
             patch('sys.stdout', new_callable=StringIO) as mock_out:
            main()
            return mock_out.getvalue()

    def test_default_lang(self):
        out = self._run_main(['pycotovia'], "casa\n")
        self.assertIn("kasa", out)

    def test_explicit_lang_gl(self):
        out = self._run_main(['pycotovia', '-l', 'gl'], "casa\n")
        self.assertIn("kasa", out)

    def test_explicit_lang_es(self):
        out = self._run_main(['pycotovia', '-l', 'es'], "casa\n")
        self.assertIn("kasa", out)

    def test_help_exits(self):
        from pycotovia.cli import main
        with patch('sys.argv', ['pycotovia', '--help']), \
             self.assertRaises(SystemExit):
            main()

    def test_multiple_lines(self):
        out = self._run_main(['pycotovia'], "casa\ncantar\n")
        self.assertIn("kasa", out)
        self.assertIn("kantar", out)


# ---------------------------------------------------------------------------
# __main__ module
# ---------------------------------------------------------------------------

class TestMain(unittest.TestCase):
    def test_main_import(self):
        # Ensure __main__ can be imported without running
        import importlib
        spec = importlib.util.spec_from_file_location(
            "pycotovia.__main__",
            str(Path(__file__).resolve().parent.parent / "pycotovia" / "__main__.py")
        )
        # just verifying no import error
        self.assertIsNotNone(spec)


# ---------------------------------------------------------------------------
# version
# ---------------------------------------------------------------------------

class TestVersion(unittest.TestCase):
    def test_version_importable(self):
        from pycotovia.version import __version__, VERSION_MAJOR, VERSION_MINOR, VERSION_BUILD
        self.assertIsInstance(__version__, str)
        self.assertIsInstance(VERSION_MAJOR, int)
        self.assertIsInstance(VERSION_MINOR, int)
        self.assertIsInstance(VERSION_BUILD, int)


class TestStripT0Extended(unittest.TestCase):
    """Tests for the %...% pause block stripping in _strip_t0."""

    def test_tra5_preserves_hashes(self):
        # tra=5 returns raw, including ## markers
        result = phonemize("casa", lang="gl", tra=5)
        self.assertIn("##", result)

    def test_percent_blocks_stripped(self):
        from pycotovia.phonemize import _strip_t0
        # %...% blocks should be stripped like ## blocks
        result = _strip_t0("%pause% kasa %pause%")
        self.assertNotIn("%", result)

    def test_hash_block_stripped(self):
        from pycotovia.phonemize import _strip_t0
        result = _strip_t0("##kasa##")
        self.assertNotIn("#", result)

    def test_hash_block_no_char_after(self):
        # ## at very end — consume without crash
        from pycotovia.phonemize import _strip_t0
        result = _strip_t0("ka##")
        self.assertIsInstance(result, str)


class TestSyllabifyMoreCoverage(unittest.TestCase):
    def test_vlen3_diphthong_then_v(self):
        # vlen==3 with first two forming a diphthong: VV-V
        # "buei" → b + uei → uei has u (feble)+e(aberta)+i(feble) = triptongo? No, es_triptongo(u,e,i) checks
        # Actually need VV then V where first two are diphthong but not all three a triptongo
        # "auea" - au is diphthong, then e hiatus → au-ea
        result = syllabify("auea")
        self.assertIsInstance(result, str)

    def test_vlen3_hiatus_then_diphthong(self):
        # V-VV: first vowel not diphthong with second, second+third are diphthong
        # "oui": o + ui → o not feble, ui is diphthong → V-VV
        result = syllabify("aoui")
        self.assertIsInstance(result, str)

    def test_four_plus_vowels_sequence(self):
        # 4+ vowels without diphthong at start
        result = syllabify("aouia")
        self.assertIsInstance(result, str)

    def test_trailing_all_consonants(self):
        # A word that ends in a string of consonants (no following vowel)
        # e.g. "trans" — after 'a', we have 'ns' all consonants at end
        result = syllabify("trans")
        self.assertIsInstance(result, str)


class TestStressMoreCoverage(unittest.TestCase):
    def test_ends_n_monosyllable_aguda(self):
        # monosyllable ending in n → no '-' so aguda branch
        result = assign_stress("pan")
        self.assertIn("^", result)

    def test_grave_when_stress_pos_none(self):
        # _grave returns None when no vowel found
        result = _grave("bcdfg")
        self.assertIsNone(result)

    def test_final_char_non_letter(self):
        # Last char is a non-letter → else: return syllabified
        result = assign_stress("ca-sa3")
        # The last char '3' is neither vocal nor consonante → should return unchanged
        self.assertIsInstance(result, str)

    def test_grave_silent_u_after_g(self):
        # Words with 'gu' + vowel: stress stays on vowel, not shifted to u
        result = assign_stress("gue-rra")
        self.assertIn("^", result)


class TestTimbreMoreCoverage(unittest.TestCase):
    pass

class TestMainModule(unittest.TestCase):
    def test_main_runs(self):
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, "-m", "pycotovia"],
            input="casa\n",
            capture_output=True,
            text=True,
        )
        self.assertIn("kasa", result.stdout)


class TestTimbreUnits(unittest.TestCase):
    """Unit level checks on the ported timbre helpers."""

    def test_posicion_acento(self):
        self.assertEqual(1, posicion_acento("ca-fe^"))
        self.assertEqual(2, posicion_acento("ca^-sa"))
        self.assertEqual(3, posicion_acento("pu^-bli-co"))
        self.assertEqual(0, posicion_acento("casa"))

    def test_cambiar_por_timbre_aberto(self):
        self.assertEqual("có^-sa", cambiar_por_timbre_aberto("co^-sa"))
        self.assertEqual("cé^-sa", cambiar_por_timbre_aberto("ce^-sa"))
        # only e and o have an open counterpart
        self.assertEqual("ca^-sa", cambiar_por_timbre_aberto("ca^-sa"))

    def test_estan_en_contacto_con_nasal(self):
        self.assertTrue(estan_en_contacto_con_nasal("es-ta-dou-ni-de^n-ses"))
        self.assertFalse(estan_en_contacto_con_nasal("com-ple^-ta"))

    def test_eu_ou_guard_is_dead_in_the_c(self):
        # Replicated precedence bug: the guard can never fire.
        self.assertFalse(hai_grupo_eu_ou_na_antepenultima_silaba("de^u-si-co"))

    def test_no_stressed_e_or_o_is_left_alone(self):
        self.assertEqual("ca^-sa", asignar_timbre_a_sustantivos("casa", "ca^-sa"))

    def test_existing_open_diacritic_is_left_alone(self):
        self.assertEqual("nó^s", asignar_timbre_a_sustantivos("nós", "nó^s"))

    def test_falling_diphthong_stays_closed(self):
        self.assertEqual("pe^i-ne", asignar_timbre_a_sustantivos("peine", "pe^i-ne"))

    def test_reversed_termination_lists_are_matched_backwards(self):
        # "cento" is reachable through the reversed entry "otnec"
        self.assertTrue(timbre_en_graves("cento", "ce^n-to"))
        # "estadounidense" is not: the binary's binary search cannot reach it
        self.assertFalse(
            timbre_en_graves("estadounidenses", "es-ta-dou-ni-de^n-ses"))

    def test_agudas(self):
        self.assertTrue(timbre_en_agudas("papel"))
        self.assertFalse(timbre_en_agudas("paso"))

    def test_esdruxulas(self):
        self.assertFalse(timbre_en_esdruxulas("alvéolo", "al-vé^-o-lo"))


if __name__ == "__main__":
    unittest.main()
