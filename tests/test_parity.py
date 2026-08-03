#!/usr/bin/env python3
"""Comprehensive parity test: pycotovia vs Cotovia binary for Galician G2P.

This test requires the Cotovia binary to be built at:
    ../cotovia-mirror/bin/cotovia

There are two oracles, and each one is paired with a pycotovia behaviour:

* the FIXED build (upstream + cotovia-mirror PR #2 and #4) at
  ../cotovia-mirror/bin/cotovia, paired with the default; and
* the PRISTINE build (stock upstream) at ../cotovia-pristine/bin/cotovia,
  paired with keep_bugs=True.

Override with COTOVIA_BIN and COTOVIA_BIN_PRISTINE. See docs/oracles.md.
Crossing the pair is meaningless and the tests never do it.

If the binary is missing, the test skips.
"""

import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pycotovia import phonemize

_SIBLING = Path(__file__).resolve().parent.parent.parent

#: The reference build: upstream plus the adjudicated fixes. Pairs with the
#: default pycotovia behaviour.
COTOVIA_BIN = Path(os.environ.get(
    "COTOVIA_BIN", _SIBLING / "cotovia-mirror" / "bin" / "cotovia"))

#: Stock upstream, defects included. Pairs with keep_bugs=True.
COTOVIA_BIN_PRISTINE = Path(os.environ.get(
    "COTOVIA_BIN_PRISTINE", _SIBLING / "cotovia-pristine" / "bin" / "cotovia"))

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
)

#: Adjudicated upstream bugs. pycotovia is deliberately different here, and
#: each entry is documented by a reference-only PR against cotovia-mirror.
#: Measured in a sentence frame. A one-letter word alone on a line loses the
#: open/closed opposition in the binary (`é` -> `e^`, but `é bo` -> `E^ Bo^`),
#: which is a separate quirk recorded in docs/parity.md.
#: (input word, pycotovia default, stock upstream, reference PR)
DELIBERATE_DIVERGENCES = (
    ("bui", "buj", "bwi", "cotovia-mirror#2"),
    ("fui", "fuj", "fwi", "cotovia-mirror#2"),
    ("cuido", "kujDo", "kwiDo", "cotovia-mirror#2"),
    ("é", "E", "e", "cotovia-mirror#4"),
)

#: Words the two builds agree on, so the fixes must not touch them. The `qu`
#: and `gu` digraphs are what the PR #2 guard exists to protect.
UNAFFECTED_BY_FIXES = ("guiar", "lingua", "aguia", "quiosco", "casa", "só")

#: Sentences in SENTENCES that contain an adjudicated divergence, so they
#: cannot be asserted equal to the binary at tra=1..3.
#: They are still asserted equal at tra=4, where the divergence disappears.
DIVERGENT_SENTENCES = frozenset({
    "el é o meu irmán",
})

#: Words in WORDS that contain an adjudicated divergence.
DIVERGENT_WORDS = frozenset({"bui", "fui", "cuido"})

#: Words where pycotovia and the binary still disagree. Each entry records
#: the binary's output so the test fails loudly if either side moves.
KNOWN_DIVERGENCES = {
    "twist": "tewi^st",     # the only w-list word still unexplained
}

#: Words that used to be in KNOWN_DIVERGENCES and now match, because the
#: binary's own list lookup and w handling are ported. Kept as guards.
CLOSED_DIVERGENCES = ("luxar", "newton", "wolfram", "darwin", "whisky")

#: Sentences for the prosodic mode (tra=4 / binary -t3).  These exercise the
#: parts of the stage that the plain phoneme levels never show: which words
#: keep their stress mark, and which stressed vowels open.
PROSODIC_SENTENCES = [
    "dixo que non o sabía de todo",
    "entre a néboa e a chuvia non se vía nada",
    "desde aquela non volveu pola aldea",
    "atopeime con eles no medio da praza",
    "quedaron connosco na porta do teatro",
    "o oso comeu o óso do animal",
    "a bóla de neve rodou pola pena",
    "colleu a póla e deixouna no chan",
    "o corpo quedou preso entre as pedras",
    "a porta da tenda estaba aberta",
    "a festa da vila foi onte pola noite",
    "puxo a mesa e serviu o caldo quente",
    "o ceo estaba limpo de nubes",
    "pagou catrocentos corenta e seis euros",
    "conta ata cento vinte e para",
    "o goberno anunciou onte as novas medidas para o sector",
    "a xente do lugar sabe ben o que quere e o que non",
    "non sei se foi el ou se foi o seu irmán quen o fixo",
]

#: Divergences that remain at -t3.  The prosodic stage depends on Cotovia's
#: morphosyntactic disambiguator and its pause/syntagma modules, neither of
#: which pycotovia ports.  Recorded so the suite fails if either side drifts.
PROSODIC_OPEN_DIVERGENCES = (
    # Verb forms: the binary resolves their timbre through
    # manexo_do_timbre_verbal() and the conjugation tables in verbos.txt.
    # pycotovia has no verb lexicon, so they fall through to the noun rules.
    "nós non sabemos nada diso",
    "vós tédelo dereito de falar",
    "o óso rompeulle bastante",
    "os ósos do animal apareceron",
    "vou colle-la maleta agora",
    "oxalá chova esta semana",
    # Tonicity of an ambiguous function word, decided by the Viterbi tagger.
    "vou dar-me unha volta",
    # Timbre and sandhi that follow from the pause and phrase-group markers
    # the binary emits at -t3 and pycotovia does not.
    "cómpre coñecer ben o camiño",
    "o ben-estar da xente importa",
    "acabouse a festa, vamos para a casa",
    # Same three causes, met in ordinary running text: most natural Galician
    # sentences contain a verb, so this is the common case rather than a
    # corner case.  See docs/parity.md for the measured rate.
    "o home da casa do fondo da rúa saíu",
    "falamos con el e mais coa súa irmá",
    "para os que non teñen nada que dicir",
    "veu por el e polos seus amigos",
    "a min non me parece ben iso",
    "chegou onda nós sen avisar a ninguén",
    "díxollelo todo sen pensalo dúas veces",
    "non llo dixo nin quixo escoitalo",
    "veu o vento forte do norte",
    "o pobre home non tiña onde durmir",
    "hai novecentos veciños censados na parroquia",
    "cando chegou a noite todos volveron para as súas casas",
)


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
            if w in DIVERGENT_WORDS:
                continue  # adjudicated bug fix — see test_deliberate_divergences
            py_result = phonemize(w, lang="gl").strip()
            bin_result = self._run_binary(w)
            if py_result != bin_result:
                failures.append((w, py_result, bin_result))

        if failures:
            msg = f"{len(failures)} / {len(UNIQUE_WORDS)} words mismatched:\n"
            for w, py, bi in failures:
                msg += f"  {w}: py={py!r} bin={bi!r}\n"
            self.fail(msg)

    #: A neutral frame. The binary treats a one-word line differently for
    #: one-letter words, so every word-level check runs inside a sentence.
    FRAME = "vin {} hoxe"

    def _framed(self, binary: Path, word: str) -> str:
        proc = subprocess.run(
            [str(binary), "-St0lgl"],
            input=self.FRAME.format(word) + "\n",
            capture_output=True, text=True, encoding="latin1")
        return proc.stdout.split()[1]

    def _framed_py(self, word: str, keep_bugs: bool = False) -> str:
        return phonemize(self.FRAME.format(word), lang="gl",
                         keep_bugs=keep_bugs).split()[1]

    def test_deliberate_divergences(self):
        """Both sides of every adjudicated bug fix are pinned.

        These are the only places where pycotovia is knowingly different from
        the binary. Each one is an upstream defect documented by a
        reference-only PR against TigreGotico/cotovia-mirror. If either side
        moves, this test fails and docs/parity.md needs an update.
        """
        for word, py_expected, _stock, pr in DELIBERATE_DIVERGENCES:
            self.assertEqual(self._framed_py(word), py_expected,
                             f"{word}: pycotovia side of {pr}")
            self.assertEqual(self._framed(COTOVIA_BIN, word), py_expected,
                             f"{word}: the fixed build must agree with the "
                             f"default. {pr}")

    def test_keep_bugs_reproduces_the_pristine_build(self):
        """keep_bugs=True must match stock upstream byte for byte."""
        if not COTOVIA_BIN_PRISTINE.exists():
            self.skipTest(f"no pristine build at {COTOVIA_BIN_PRISTINE}")
        for word, _py, stock, pr in DELIBERATE_DIVERGENCES:
            self.assertEqual(self._framed_py(word, keep_bugs=True), stock,
                             f"{word}: keep_bugs side of {pr}")
            self.assertEqual(self._framed(COTOVIA_BIN_PRISTINE, word), stock,
                             f"{word}: pristine build side of {pr}")

    def test_the_fixes_touch_nothing_else(self):
        """Both builds, and both pycotovia modes, agree on everything else."""
        for word in UNAFFECTED_BY_FIXES:
            default = self._framed_py(word)
            self.assertEqual(self._framed_py(word, keep_bugs=True), default, word)
            self.assertEqual(self._framed(COTOVIA_BIN, word), default, word)
            if COTOVIA_BIN_PRISTINE.exists():
                self.assertEqual(self._framed(COTOVIA_BIN_PRISTINE, word),
                                 default, word)

    def test_pr2_precedence_fix_is_present(self):
        """cotovia-mirror PR #2: `*p-2` vs `p[-2]` in aguda() and grave().

        `(*p-2)=='g'` is `((*p)-2)=='g'`, which is always true when `*p` is
        'i' (0x69 - 2 == 0x67 == 'g'). The guard that should protect the
        silent `u` of `qu`/`gu` therefore fires for every `i`, and the stress
        never moves back onto the first vowel of a rising `ui` diphthong.

        pycotovia reads the character two positions back, as intended.
        """
        # The fix only changes rising ui: stress lands on u, i becomes a glide.
        self.assertEqual(phonemize("bui", lang="gl", tra=2).strip(), "bu^j")
        self.assertEqual(phonemize("cuido", lang="gl", tra=2).strip(), "ku^jDo")
        # The silent u of gu/qu is still protected — the guard's real purpose.
        self.assertEqual(phonemize("guiar", lang="gl", tra=2).strip(), "gja^r")
        self.assertEqual(phonemize("lingua", lang="gl", tra=2).strip(), "li^Ngwa")

    def test_pr4_diacritic_off_by_one_fix_is_present(self):
        """cotovia-mirror PR #4: `cont++` in the guard of the diacritic loop.

        The guard tests entry N while the body compares entry N+1, so entry 0
        ("é") is never compared and the "\\0" terminator is compared instead.
        pycotovia keeps "é" in the table.
        """
        self.assertEqual(phonemize("é bo", lang="gl", tra=2).split()[0], "E^")
        # The entries the C loop does reach must keep working.
        self.assertEqual(phonemize("ó bo", lang="gl", tra=2).split()[0], "O^")
        self.assertEqual(phonemize("só bo", lang="gl", tra=2).split()[0], "sO^")
        # And a word that is not in the table must not open.
        self.assertEqual(phonemize("café bo", lang="gl", tra=2).split()[0], "kafe^")

    def test_diacritic_fix_does_not_change_the_prosodic_mode(self):
        """The PR #4 fix must cost nothing at tra=4.

        The prosodic stage opens "é" to E^ on its own, so the mode the
        Cotovia-alphabet voices were trained on is identical either way.
        This is the reason the fix is safe to take. See docs/parity.md.
        """
        sentence = "el é o meu irmán"
        self.assertEqual(phonemize(sentence, lang="gl", tra=4).split(),
                         self._run_binary_t3(sentence))

    def _run_binary_sentence(self, sentence: str, mode: str) -> str:
        proc = subprocess.run(
            [str(COTOVIA_BIN), f"-S{mode}lgl"],
            input=sentence + "\n",
            capture_output=True,
            text=True,
            encoding="latin1",
        )
        return " ".join(proc.stdout.split())

    def _run_binary_t3(self, sentence: str) -> list[str]:
        """Binary -t3 output with the pause and phrase-group markers removed."""
        proc = subprocess.run(
            [str(COTOVIA_BIN), "-St3lgl"],
            input=sentence + "\n",
            capture_output=True,
            text=True,
            encoding="latin1",
        )
        out = re.sub(r"#%[^%]*%#", "", proc.stdout)
        out = re.sub(r"%[^%]*%", "", out)
        return out.split()

    def test_sentences_match_binary_with_stress(self):
        """pycotovia tra=2 must equal the binary's -t1 (phonemes + stress)."""
        failures = []
        for sentence in SENTENCES:
            if sentence in DIVERGENT_SENTENCES:
                continue  # adjudicated bug fix — see test_deliberate_divergences
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
            if sentence in DIVERGENT_SENTENCES:
                continue  # adjudicated bug fix — see test_deliberate_divergences
            py = " ".join(phonemize(sentence, lang="gl", tra=3).split())
            binary = self._run_binary_sentence(sentence, "t2")
            if py != binary:
                failures.append((sentence, py, binary))
        if failures:
            msg = f"{len(failures)} / {len(SENTENCES)} sentences mismatched:\n"
            for s, py, bi in failures:
                msg += f"  {s!r}\n    py ={py!r}\n    bin={bi!r}\n"
            self.fail(msg)

    def test_closed_divergences_match_the_binary(self):
        """Words the ported list lookup and w handling fixed. Guard them."""
        for word in CLOSED_DIVERGENCES:
            sentence = f"vin {word} hoxe"
            self.assertEqual(
                phonemize(sentence, lang="gl", tra=2).split()[1],
                self._run_binary_sentence(sentence, "t1").split()[1],
                word,
            )

    def test_contraction_ao_matches_the_binary(self):
        """preproc.cpp rewrites `ao`/`aos` as `ó`/`ós` before anything else."""
        for sentence in ("foi ao mar", "foi aos mares", "puxo o anexo ao final"):
            self.assertEqual(
                " ".join(phonemize(sentence, lang="gl", tra=2).split()),
                self._run_binary_sentence(sentence, "t1"),
                sentence,
            )

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


    def test_prosodic_sentences_match_binary(self):
        """pycotovia tra=4 must equal the binary's -t3 prosodic output.

        The binary also prints pause and phrase-group markers at -t3; those
        need modules pycotovia does not port, so they are stripped before
        comparing.
        """
        failures = []
        for sentence in PROSODIC_SENTENCES:
            py = phonemize(sentence, lang="gl", tra=4).split()
            binary = self._run_binary_t3(sentence)
            if py != binary:
                failures.append((sentence, py, binary))
        if failures:
            msg = f"{len(failures)} / {len(PROSODIC_SENTENCES)} mismatched:\n"
            for s, py, bi in failures:
                msg += f"  {s!r}\n    py ={py}\n    bin={bi}\n"
            self.fail(msg)

    def test_prosodic_mode_destresses_function_words(self):
        """The whole point of the stage: function words lose their mark."""
        plain = phonemize("a defensa faina ese goberno", lang="gl", tra=3)
        prosodic = phonemize("a defensa faina ese goberno", lang="gl", tra=4)
        self.assertTrue(plain.startswith("a^"))
        self.assertTrue(prosodic.startswith("a "))
        # and nouns get their open vowels
        self.assertIn("E^", prosodic)
        self.assertNotIn("E^", plain)

    def test_prosodic_open_divergences_are_still_divergent(self):
        """Guard the -t3 gaps: the binary's side must not drift."""
        for sentence in PROSODIC_OPEN_DIVERGENCES:
            self.assertNotEqual(
                phonemize(sentence, lang="gl", tra=4).split(),
                self._run_binary_t3(sentence),
                f"{sentence!r} now matches — remove it from "
                "PROSODIC_OPEN_DIVERGENCES",
            )


if __name__ == "__main__":
    unittest.main()
