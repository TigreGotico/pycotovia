#!/usr/bin/env python3
"""Basic unit tests for pycotovia."""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pycotovia import phonemize, Phonemizer, cotovia_to_ipa
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
        self.assertEqual(phonemize("México", lang="es").strip(), "Meksiko")
        self.assertEqual(phonemize("México", lang="gl").strip(), "MeSiko")

    def test_w_exception(self):
        """w → gu in some loanwords."""
        self.assertEqual(phonemize("sandwich", lang="es").strip(), "sanDwis")

    def test_phrase(self):
        """Whitespace and punctuation are stripped."""
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
        self.assertEqual(assign_stress("can-tar"), "can-tar")

    def test_grave(self):
        self.assertEqual(assign_stress("ca-sa"), "ca^-sa")

    def test_orthographic_accent(self):
        self.assertEqual(assign_stress("ca-fé"), "ca-fé")

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
        self.assertEqual(cotovia_to_ipa("gerra"), "ɣɛra")

    def test_double(self):
        self.assertEqual(cotovia_to_ipa("tSa"), "tʃa")
        self.assertEqual(cotovia_to_ipa("rra"), "ra")


if __name__ == "__main__":
    unittest.main()
