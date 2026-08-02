#!/usr/bin/env python3
"""Basic unit tests for pycotovia."""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pycotovia import phonemize, Phonemizer, cotovia_to_ipa, ALPHABETS, AlphabetError, UnmappedSymbolError
from pycotovia.syllabify import syllabify
from pycotovia.stress import assign_stress
from pycotovia.charset import vocal, consonante, es_diptongo, es_triptongo


class TestPhonemize(unittest.TestCase):
    def test_galician_basic(self):
        self.assertEqual(phonemize("casa", lang="gl"), "kasa ")
        self.assertEqual(phonemize("cantar", lang="gl"), "kantar ")

    def test_spanish_basic(self):
        self.assertEqual(phonemize("casa", lang="es"), "kasa ")
        self.assertEqual(phonemize("cantar", lang="es"), "kantar ")

    def test_x_exception(self):
        """Spanish x → ks, Galician x → S."""
        self.assertEqual(phonemize("México", lang="es").strip(), "meksiko")
        self.assertEqual(phonemize("México", lang="gl").strip(), "meSiko")

    def test_w_exception(self):
        """w → gu in some loanwords (Cotovia output)."""
        self.assertEqual(phonemize("sandwich", lang="es").strip(), "sandGitS")

    def test_phrase(self):
        """Whitespace and punctuation are stripped, words are lowercased."""
        self.assertEqual(phonemize("Ola, mundo!", lang="gl").strip(), "ola mundo")

    def test_tra_levels(self):
        """Output levels control stripping."""
        self.assertEqual(phonemize("guerra", lang="gl", tra=1).strip(), "gerra")
        self.assertIn("^", phonemize("guerra", lang="gl", tra=2))
        self.assertIn("-", phonemize("guerra", lang="gl", tra=3))
        self.assertIn("#", phonemize("guerra", lang="gl", tra=4))

    def test_reuse_phonemizer(self):
        p = Phonemizer(lang="gl")
        self.assertEqual(p.phonemize("casa").strip(), "kasa")
        self.assertEqual(p.phonemize("cantar").strip(), "kantar")


class TestAlphabets(unittest.TestCase):
    def test_default_is_native_cotovia(self):
        """Parity: the default call is byte-identical to pre-scriptconv output."""
        self.assertEqual(phonemize("casa", lang="gl"), "kasa ")
        self.assertEqual(phonemize("guerra", lang="gl"), "gerra ")
        self.assertEqual(phonemize("casa", lang="gl", alphabet="cotovia"), "kasa ")

    def test_alphabets_enumerated_from_scriptconv(self):
        self.assertIn("cotovia", ALPHABETS)
        self.assertIn("ipa", ALPHABETS)
        self.assertIn("x-sampa", ALPHABETS)

    def test_ipa_output(self):
        self.assertEqual(phonemize("casa", lang="gl", alphabet="ipa").strip(), "kasa")
        self.assertEqual(phonemize("guerra", lang="gl", alphabet="ipa").strip(), "ɡera")
        self.assertEqual(phonemize("luz", lang="gl", alphabet="ipa").strip(), "luθ")
        self.assertEqual(phonemize("xente", lang="gl", alphabet="ipa").strip(), "ʃente")
        self.assertEqual(phonemize("chave", lang="gl", alphabet="ipa").strip(), "tʃaβe")
        self.assertEqual(phonemize("México", lang="es", alphabet="ipa").strip(), "meksiko")

    def test_x_sampa_output(self):
        """Spot check: X-SAMPA agrees with IPA for the tap ɾ, e.g. in 'cantar'."""
        self.assertEqual(phonemize("cantar", lang="gl", alphabet="x-sampa").strip(), "kanta4")
        self.assertEqual(phonemize("casa", lang="gl", alphabet="x-sampa").strip(), "kasa")

    def test_unsupported_alphabet_raises(self):
        with self.assertRaises(AlphabetError):
            phonemize("casa", lang="gl", alphabet="klingon")

    def test_unmapped_symbol_raises_not_silently_dropped(self):
        """ARPABET has no symbol for the voiced bilabial approximant/fricative
        β (Galician intervocalic b/v, e.g. 'vivir' -> biβiɾ). This is an
        inherent gap — ARPA's inventory is built for English phonology, which
        has no β — not a scriptconv omission that will ever be "fixed", so
        it fails loudly instead of being dropped or mistranslated."""
        with self.assertRaises(UnmappedSymbolError):
            phonemize("vivir", lang="gl", alphabet="arpa")

    def test_alphabet_requires_tra1(self):
        with self.assertRaises(AlphabetError):
            phonemize("guerra", lang="gl", tra=2, alphabet="ipa")


class TestSyllabify(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(syllabify("casa"), "ca-sa")
        self.assertEqual(syllabify("cantar"), "can-tar")

    def test_diphthong(self):
        self.assertEqual(syllabify("guerra"), "gue-rra")
        self.assertEqual(syllabify("seguir"), "se-guir")

    def test_triphthong(self):
        self.assertEqual(syllabify("guia"), "guia")
        self.assertEqual(syllabify("guion"), "guion")


class TestStress(unittest.TestCase):
    def test_aguda(self):
        self.assertEqual(assign_stress("can-tar"), "can-ta^r")

    def test_grave(self):
        self.assertEqual(assign_stress("ca-sa"), "ca^-sa")

    def test_orthographic_accent(self):
        self.assertEqual(assign_stress("ca-fé"), "ca-fe^")

    def test_correct_ui(self):
        """bui, fui, cuido stress on u (correct)."""
        self.assertEqual(assign_stress("bui"), "bu^i")
        self.assertEqual(assign_stress("fui"), "fu^i")
        self.assertEqual(assign_stress("cui-do"), "cu^i-do")


class TestCharset(unittest.TestCase):
    def test_vowel(self):
        self.assertTrue(vocal("a"))
        self.assertTrue(vocal("e"))
        self.assertTrue(vocal("A"))
        self.assertFalse(vocal("b"))

    def test_consonante(self):
        self.assertTrue(consonante("b"))
        self.assertFalse(consonante("a"))

    def test_diptongo(self):
        self.assertTrue(es_diptongo("a", "i"))
        self.assertTrue(es_diptongo("u", "a"))
        self.assertFalse(es_diptongo("a", "e"))

    def test_triptongo(self):
        self.assertTrue(es_triptongo("u", "i", "a"))
        self.assertTrue(es_triptongo("u", "e", "i"))
        self.assertFalse(es_triptongo("a", "e", "i"))


class TestIPA(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(cotovia_to_ipa("kasa"), "kasa")
        self.assertEqual(cotovia_to_ipa("gerra"), "ɡera")

    def test_double(self):
        self.assertEqual(cotovia_to_ipa("tSa"), "tʃa")
        self.assertEqual(cotovia_to_ipa("rra"), "ra")


if __name__ == "__main__":
    unittest.main()
