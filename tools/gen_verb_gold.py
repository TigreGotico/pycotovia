#!/usr/bin/env python3
"""Freeze the binary's verb analysis as test gold.

Runs every word of a corpus through `cotovia -SL1lgl` inside a neutral frame
and records the lemmas it offers as verb readings. The result is test gold
only; the analyser never consults it at runtime.

Usage::

    python3 tools/gen_verb_gold.py corpus.txt \\
        --binary ../cotovia-mirror/bin/cotovia \\
        --output tests/gold/verb_lemmas.tsv
"""

import argparse
import re
import subprocess
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

_BINARY = None


def _init(binary):
    global _BINARY
    _BINARY = binary


def _analyse(word):
    proc = subprocess.run(
        [_BINARY, "-SL1lgl"], input=f"vin {word} hoxe.\n",
        capture_output=True, encoding="latin1", errors="replace")
    for line in proc.stdout.split("\n"):
        fields = line.split("\t")
        if fields and fields[0] == word:
            # The lemma is the field after each "N CONXUGACION" field.
            return word, sorted({fields[i + 1].strip()
                                 for i in range(len(fields) - 1)
                                 if "CONXUGACI" in fields[i]})
    return word, []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--binary", type=Path,
                        default=Path("../cotovia-mirror/bin/cotovia"))
    parser.add_argument("--output", type=Path,
                        default=Path("tests/gold/verb_lemmas.tsv"))
    args = parser.parse_args()

    vocab = set()
    for line in args.corpus.read_text(encoding="utf-8").splitlines():
        vocab.update(re.findall(r"[a-záéíóúüñç]+", line.lower()))
    words = sorted(vocab)

    with ProcessPoolExecutor(16, initializer=_init,
                             initargs=(str(args.binary),)) as pool:
        rows = list(pool.map(_analyse, words, chunksize=40))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# word\\tlemma,lemma  — verb readings from cotovia -SL1lgl",
             f"# corpus: {args.corpus.name}, {len(words)} types"]
    kept = 0
    for word, lemmas in rows:
        if lemmas:
            lines.append(f"{word}\t{','.join(lemmas)}")
            kept += 1
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{args.output}: {kept} words with a verb reading, of {len(words)}")


if __name__ == "__main__":
    main()
