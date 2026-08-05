#!/usr/bin/env python3
"""Verb analyser tests.

The gold is the binary's own morphological analysis (`-L1`), which prints the
lemma, tense, person and conjugation for every reading it finds. It is read
from the binary, never written by hand.

`tests/gold/verb_lemmas.tsv` holds a frozen extract of that output so the bulk
check runs without the binary. Regenerate it with
`tools/gen_verb_gold.py`.
"""

import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pycotovia.morphology import (analizar_verbo, detectar_desinencias_verbais,
                                  eliminar_encliticos, e_verbo,
                                  quitar_acento_de_enclitico)

_SIBLING = Path(__file__).resolve().parent.parent.parent
COTOVIA_BIN = Path(os.environ.get(
    "COTOVIA_BIN", _SIBLING / "cotovia-mirror" / "bin" / "cotovia"))
GOLD = Path(__file__).resolve().parent / "gold" / "verb_lemmas.tsv"


def lemmas(word):
    return {a.infinitivo for a in analizar_verbo(word)}


class TestVerbAnalysis(unittest.TestCase):
    """Readings the prosodic stage depends on."""

    def test_regular_forms(self):
        self.assertEqual(lemmas("cantamos"), {"cantar"})
        self.assertEqual(lemmas("abordaba"), {"abordar"})
        self.assertEqual(lemmas("partiu"), {"partir"})

    def test_the_verbs_the_timbre_gap_was_made_of(self):
        """These are the forms docs/parity.md lists as verb-timbre failures."""
        self.assertEqual(lemmas("sabemos"), {"saber"})
        self.assertEqual(lemmas("volveron"), {"volver"})
        self.assertEqual(lemmas("chova"), {"chover"})
        self.assertEqual(lemmas("teñen"), {"ter"})
        self.assertEqual(lemmas("lemos"), {"ler"})

    def test_irregular_forms_have_no_separable_root(self):
        """`foron` is both ir and ser. Both come from the "0"-root branch."""
        analises = analizar_verbo("foron")
        self.assertEqual({a.infinitivo for a in analises}, {"ir", "ser"})
        self.assertTrue(all(a.raiz == "" for a in analises))

    def test_a_root_can_carry_two_infinitives(self):
        """verbos.txt: `abrac,abracar,4,abrazar,5`."""
        self.assertEqual(lemmas("abracamos"), {"abracar"})

    def test_nouns_are_not_verbs(self):
        for word in ("mesa", "café", "muller", "cidade"):
            self.assertEqual(analizar_verbo(word), [], word)

    def test_ambiguous_forms_return_every_reading(self):
        """`casa` is a noun and a form of `casar`. Deciding is the tagger's
        job, so the analyser must offer the verb reading."""
        self.assertIn("casar", lemmas("casa"))

    def test_model_and_tense_are_reported(self):
        analise = analizar_verbo("sabemos")[0]
        self.assertEqual(analise.infinitivo, "saber")
        self.assertEqual(analise.desinencia, "emos")
        self.assertIsInstance(analise.modelo, int)
        self.assertIsInstance(analise.tempo, int)

    def test_e_verbo(self):
        self.assertTrue(e_verbo("cantamos"))
        self.assertFalse(e_verbo("mesa"))


class TestEndings(unittest.TestCase):

    def test_shorter_endings_are_found_too(self):
        """The C keeps searching before the entry it found, so `abades`
        offers both `-abades` and `-ades`."""
        found = [d.desinencia for d in detectar_desinencias_verbais("cantabades")]
        self.assertIn("abades", found)
        self.assertIn("ades", found)

    def test_pairs_are_tense_then_model(self):
        for d in detectar_desinencias_verbais("cantamos"):
            for tempo, modelo in d.pares():
                self.assertIsInstance(tempo, int)
                self.assertIsInstance(modelo, int)


class TestEnclitics(unittest.TestCase):

    def test_the_bare_form_comes_first(self):
        self.assertEqual(eliminar_encliticos("canta")[0], ("canta", ""))

    def test_nested_enclitics(self):
        found = dict(eliminar_encliticos("dállelo"))
        self.assertIn("dá", found)

    def test_forms_with_enclitics_analyse(self):
        self.assertEqual(lemmas("aceptalo"), {"aceptar"})
        self.assertEqual(lemmas("dállelo"), {"dar"})

    def test_the_accent_an_enclitic_adds_is_undone(self):
        """`accede` + `se` is spelled `accédese`. The root dictionary has
        `acced`, so the accent has to come off before the lookup."""
        self.assertEqual(quitar_acento_de_enclitico("accéde"), "accede")
        self.assertEqual(lemmas("accédese"), {"acceder"})
        self.assertEqual(lemmas("adóitase"), {"adoitar"})
        self.assertEqual(lemmas("adaptáronse"), {"adaptar"})

    def test_a_real_graphic_accent_is_kept(self):
        """`cantará` is spelled that way regardless of enclitics."""
        self.assertIsNone(quitar_acento_de_enclitico("cantará"))


class TestNonVerbExceptions(unittest.TestCase):

    def test_excepciones_verbos_is_honoured(self):
        """`excep_verbo()` blocks words that parse as verb forms but are not."""
        self.assertEqual(analizar_verbo("arbórea"), [])
        self.assertEqual(analizar_verbo("arxéntea"), [])


@unittest.skipUnless(GOLD.exists(), f"no gold at {GOLD}")
class TestAgainstBinaryGold(unittest.TestCase):
    """Bulk check against the binary's own analysis.

    The gold is a frozen extract of `cotovia -SL1lgl` over the vocabulary of
    the parity corpus. The threshold guards against regression; it is not a
    claim of completeness. docs/parity.md carries the current rate and names
    what the remainder is.
    """

    #: Measured at 92.72% when the gold was frozen. Kept a little below so a
    #: rounding change does not fail the suite, but any real regression does.
    MINIMUM_AGREEMENT = 0.92

    def test_lemma_sets_match_the_binary(self):
        total = agree = 0
        disagreements = []
        for line in GOLD.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            word, _, joined = line.partition("\t")
            gold = set(filter(None, joined.split(",")))
            got = lemmas(word)
            if not gold and not got:
                continue
            total += 1
            if gold == got:
                agree += 1
            elif len(disagreements) < 20:
                disagreements.append((word, sorted(got), sorted(gold)))

        rate = agree / total
        self.assertGreaterEqual(
            rate, self.MINIMUM_AGREEMENT,
            f"agreement fell to {rate:.4f} ({agree}/{total}). "
            f"First disagreements: {disagreements}")


@unittest.skipUnless(COTOVIA_BIN.exists(), f"no binary at {COTOVIA_BIN}")
class TestGoldIsStillTrue(unittest.TestCase):
    """The frozen gold must still be what the binary says."""

    SAMPLE = ("sabemos", "chova", "teñen", "foron", "accédese", "casa", "mesa")

    def test_sample_matches_the_live_binary(self):
        for word in self.SAMPLE:
            proc = subprocess.run(
                [str(COTOVIA_BIN), "-SL1lgl"], input=f"vin {word} hoxe.\n",
                capture_output=True, encoding="latin1", errors="replace")
            gold = set()
            for line in proc.stdout.split("\n"):
                fields = line.split("\t")
                if fields and fields[0] == word:
                    gold = {fields[i + 1].strip()
                            for i in range(len(fields) - 1)
                            if "CONXUGACI" in fields[i]}
            self.assertEqual(lemmas(word), gold, word)


if __name__ == "__main__":
    unittest.main()
