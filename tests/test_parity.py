#!/usr/bin/env python3
"""Comprehensive parity test: pycotovia vs Cotovia binary for Galician G2P.

This test requires the Cotovia binary to be built at:
    ../cotovia-mirror/bin/cotovia

If the binary is missing, the test skips.
"""

import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pycotovia import phonemize

# Path to the Cotovia binary
COTOVIA_BIN = Path(__file__).resolve().parent.parent.parent / "cotovia-mirror" / "bin" / "cotovia"

WORDS = [
    "casa", "cantar", "canon", "canons",
    "pais", "maiz", "cafe", "publico",
    "politica", "politico", "economico", "economica",
    "fui", "cuido", "canto", "cantei", "cantamos",
    "buey", "aislado", "aereo", "oasis",
    "fe", "si", "tu", "yo",
    "hola", "adios", "gracias", "por",
    "que", "quien", "como", "cuando",
    "donde", "cual", "cuanto", "cuales",
    "aun", "aunque",
    "europa", "europeo", "europea",
    "audio", "audiencia", "audiovisual",
    "ciencia", "ciencias", "cien",
    "diez", "dieciocho", "dient",
    "viento", "vientos", "vientre",
    "pie", "pies", "piel", "piedra",
    "miel", "miedo",
    "bien", "bienes", "bienvenido",
    "quien", "quienes", "quienquiera",
    "quince", "quincena", "quincuagesimo",
    "guante", "guantes", "guapo", "guapa",
    "guerra", "guerras", "guerrero", "guerrera",
    "guia", "guias", "guion", "guiones",
    "bui", "buio",
    "lingua", "linguas", "linguista",
    "quilo", "quilos", "quilogramo",
    "seguir", "seguin", "segundo",
    "pais", "paises", "maiz", "maices",
]

# Deduplicate while preserving order
seen = set()
UNIQUE_WORDS = []
for w in WORDS:
    if w not in seen:
        seen.add(w)
        UNIQUE_WORDS.append(w)


# ---------------------------------------------------------------------------
# Sentence-level parity corpus.
#
# Real Galician sentences, one group per defect class fixed in
# fix/stress-timbre-parity.  The gold is not written down here: every
# expectation is computed by running the C binary, which is the oracle.
# ---------------------------------------------------------------------------

SENTENCES = [
    # -- open/closed vowel opposition (diacriticos_oposicion_aberta_pechada) --
    "ó neno gustoulle o conto",
    "deulles ós rapaces a merenda",
    "nós non sabemos nada diso",
    "vós tédelo dereito de falar",
    "el vén mañá pola tarde",
    "ti vés comigo ou quedas",
    "só quero saber a verdade",
    "a sé do bispado está pechada",
    "tén conta do que dis",
    "quero un té con limón",
    "o nó da corda apertouse moito",
    "sentiu un dó fondo no peito",
    "a bóla rodou ata o río",
    "as bólas de vidro son bonitas",
    "a póla da árbore rompeu",
    "o óso rompeulle bastante",
    "cómpre falar con calma",
    "tiña présa por chegar",
    # closed counterparts — these must NOT open
    "el é o meu irmán",
    "ti és moi teimudo",
    "os ósos do animal apareceron",
    "quedaron sós na casa",
    "a miña avó vive na aldea",
    "tomamos un café na praza",

    # -- ñ and ç must survive accent stripping (ACENTO_A_BASE) --
    "a compañía chegou onte pola mañá",
    "a señá do pazo saudou os veciños",
    "teñén moito que contar despois",
    "o cañón do río impresiona a quen o ve",
    "cómpre coñecer ben o camiño",
    "espiñá o dedo coa silva",
    "botou açúcar de máis no café",
    "comeu unha maçá pola tarde",
    "mañán imos á feira do gando",

    # -- hyphenated clitics: -lo/-la/-los/-las join, everything else splits --
    "quero amosa-lo camiño",
    "vou colle-la maleta agora",
    "hai que pecha-los ollos",
    "convén regar-las plantas",
    "quero amosa-lle o camiño",
    "vou dar-me unha volta",
    "o ben-estar da xente importa",
    "penso conta-lo todo",

    # -- x family: terminal -x, próxi-, and the con-xe exceptions --
    "o próximo martes hai reunión",
    "os próximos días van ser duros",
    "a proximidade do mar nótase",
    "colleu un taxi ata o porto",
    "mandoulle un fax pola mañá",
    "o tórax molestoulle bastante",
    "atopamos un anaco de ónix",
    "necesito relax despois do traballo",
    "consultou o índex do libro",
    "o exército desfilou pola rúa",
    "oxalá chova esta semana",
    "o exame foi moi difícil",
    "un texto complexo de ler",
    "puxo o anexo no final",

    # -- sentence separators reset the phrase-initial sandhi --
    "donas e cabaleiros: voulles amosa-lo home máis forte do mundo.",
    "chegou tarde: vaise queixar diso",
    "non o vin; volveu sen avisar",
    "acabouse a festa. vamos para a casa",
    "acabouse a festa, vamos para a casa",

    # -- function words, clitics and contractions in running text --
    "a defensa institucional faina ese goberno e quen goberne",
    "supoño que iso fala dos poucos argumentos que hai enriba da mesa",
    "como van executar todas estas funcións que lles están a pedir",
    "hai xiros da linguaxe con sentido figurado que non deben interpretarse",
    "deuvolvo o libro que me emprestaches onte pola noite",
]

#: Words where pycotovia and the binary still disagree.  Each entry records
#: the binary's output so the test fails loudly if the behaviour shifts.
#: See docs/parity.md for the diagnosis of each.
#: Sentences that expose divergences found while building this corpus but
#: outside the scope of fix/stress-timbre-parity.  They are recorded here,
#: not asserted, so the next pass has a starting point.  See docs/parity.md.
OPEN_DIVERGENCE_SENTENCES = (
    # Hiatus after a stressed í is not split: "doíalle" at tra=3 gives
    # py "Do-i^a-Ze" where the binary has "Do-i^-a-Ze".
    "o óso doíalle bastante",
    # The contraction "ao"/"aos" is a lexical open O in the binary ("O^"),
    # but pycotovia transcribes it literally as "a^-o".
    "puxo o anexo ao final",
)

KNOWN_DIVERGENCES = {
    "luxar": "luSa^r",      # prefix match vs the binary's binary search
    "twist": "tewi^st",     # w exception lists
    "newton": "ne^BtoN",
    "wolfram": "bolfra^m",
}


@unittest.skipUnless(COTOVIA_BIN.exists(), f"Cotovia binary not found at {COTOVIA_BIN}")
class TestParity(unittest.TestCase):
    """Verify pycotovia output matches the Cotovia binary."""

    def _run_binary(self, word: str) -> str:
        proc = subprocess.run(
            [str(COTOVIA_BIN), "-St0lgl"],
            input=word + "\n",
            capture_output=True,
            text=True,
            encoding="latin1",
        )
        return proc.stdout.strip()

    def test_all_words(self):
        failures = []
        for w in UNIQUE_WORDS:
            py_result = phonemize(w, lang="gl").strip()
            bin_result = self._run_binary(w)
            if py_result != bin_result:
                failures.append((w, py_result, bin_result))

        if failures:
            msg = f"{len(failures)} / {len(UNIQUE_WORDS)} words mismatched:\n"
            for w, py, bi in failures:
                msg += f"  {w}: py={py!r} bin={bi!r}\n"
            self.fail(msg)

    def test_ui_diphthong_matches_binary(self):
        """bui/fui/cuido: pycotovia and the binary agree.

        docs/parity.md used to list these three words as deliberate
        divergences, on the grounds that a `*p-2` vs `*(p-2)` precedence bug
        in the C aguda()/grave() made the binary emit `bwi`/`fwi`/`kwiDo`.
        The binary does not do that — it emits the same forms pycotovia does.
        There are no deliberate divergences left.
        """
        for w, expected in (("bui", "buj"), ("fui", "fuj"), ("cuido", "kujDo")):
            self.assertEqual(phonemize(w, lang="gl").strip(), expected, w)
            self.assertEqual(self._run_binary(w), expected, w)

    def _run_binary_sentence(self, sentence: str, mode: str) -> str:
        proc = subprocess.run(
            [str(COTOVIA_BIN), f"-S{mode}lgl"],
            input=sentence + "\n",
            capture_output=True,
            text=True,
            encoding="latin1",
        )
        return " ".join(proc.stdout.split())

    def test_sentences_match_binary_with_stress(self):
        """pycotovia tra=2 must equal the binary's -t1 (phonemes + stress)."""
        failures = []
        for sentence in SENTENCES:
            py = " ".join(phonemize(sentence, lang="gl", tra=2).split())
            binary = self._run_binary_sentence(sentence, "t1")
            if py != binary:
                failures.append((sentence, py, binary))
        if failures:
            msg = f"{len(failures)} / {len(SENTENCES)} sentences mismatched:\n"
            for s, py, bi in failures:
                msg += f"  {s!r}\n    py ={py!r}\n    bin={bi!r}\n"
            self.fail(msg)

    def test_sentences_match_binary_with_syllables(self):
        """pycotovia tra=3 must equal the binary's -t2 (+ syllable separators)."""
        failures = []
        for sentence in SENTENCES:
            py = " ".join(phonemize(sentence, lang="gl", tra=3).split())
            binary = self._run_binary_sentence(sentence, "t2")
            if py != binary:
                failures.append((sentence, py, binary))
        if failures:
            msg = f"{len(failures)} / {len(SENTENCES)} sentences mismatched:\n"
            for s, py, bi in failures:
                msg += f"  {s!r}\n    py ={py!r}\n    bin={bi!r}\n"
            self.fail(msg)

    def test_known_divergences_are_still_divergent(self):
        """Guard the open divergences: the binary's side must not drift."""
        for word, expected_bin in KNOWN_DIVERGENCES.items():
            got = self._run_binary_sentence(f"vin {word} hoxe", "t1").split()[1]
            self.assertEqual(got, expected_bin, word)
            self.assertNotEqual(
                phonemize(f"vin {word} hoxe", lang="gl", tra=2).split()[1],
                expected_bin,
                f"{word} now matches the binary — remove it from KNOWN_DIVERGENCES",
            )


if __name__ == "__main__":
    unittest.main()
