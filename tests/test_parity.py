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

    def test_deliberate_divergences(self):
        """Document the 3 known divergences (C source bug)."""
        divergences = {
            "bui": ("buj", "bwi"),
            "fui": ("fuj", "fwi"),
            "cuido": ("kujDo", "kwiDo"),
        }
        for w, (expected_py, expected_bin) in divergences.items():
            py_result = phonemize(w, lang="gl").strip()
            bin_result = self._run_binary(w)
            self.assertEqual(py_result, expected_py)
            self.assertEqual(bin_result, expected_bin)


if __name__ == "__main__":
    unittest.main()
