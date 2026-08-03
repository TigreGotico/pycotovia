#!/usr/bin/env python3
"""Corpus parity harness: pycotovia against the Cotovia binary at every mode.

The binary is the oracle. This tool runs a plain-text corpus (one sentence per
line) through both, at every `tra` level, and reports word-level and
sentence-level agreement. Every number in `docs/parity.md` comes from here.

Two binaries may be given:

* `--binary` — the upstream binary, built from an unmodified `cotovia-mirror`
  checkout. This is the oracle.
* `--binary-fixed` — optional. A binary built from a checkout that carries the
  adjudicated bug fixes (see `docs/parity.md`). Comparing the two measures the
  blast radius of each fix.

Usage::

    python3 tools/parity_harness.py corpus.txt \\
        --binary ../cotovia-mirror/bin/cotovia \\
        --binary-fixed ../cotovia-fixed/bin/cotovia

Note that the binary reads Latin-1 and writes Latin-1, and that it must be
called one sentence per process: piping many lines in at once makes it merge
some of them.
"""

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pycotovia import phonemize  # noqa: E402

#: Pause and phrase-group markers. The binary prints these at `-t3`; they come
#: from the pause and syntagma modules. They are stripped before comparing.
MARKERS = re.compile(r"#%[^%]*%#|%[^%]*%")

_BINARY = None
_MODE = None


def _init(binary, mode):
    global _BINARY, _MODE
    _BINARY, _MODE = binary, mode


def _run_one(sentence):
    proc = subprocess.run(
        [_BINARY, f"-St{_MODE}lgl"],
        input=sentence.strip() + ".\n",
        capture_output=True,
        encoding="latin1",
        errors="replace",
    )
    return proc.stdout


def run_binary(binary, sentences, mode, workers=16):
    """Run the binary over every sentence at `-t<mode>`."""
    with ProcessPoolExecutor(workers, initializer=_init,
                             initargs=(str(binary), mode)) as pool:
        return list(pool.map(_run_one, sentences, chunksize=20))


def normalise(text, strip_markers=False):
    if strip_markers:
        text = MARKERS.sub(" ", text)
    return " ".join(text.split())


def score(predicted, gold):
    """Compare two lists of transcriptions word by word and sentence by sentence."""
    sentences_ok = 0
    words_ok = words_total = 0
    diffs = Counter()
    for pred, ref in zip(predicted, gold):
        if pred == ref:
            sentences_ok += 1
        pred_words, ref_words = pred.split(), ref.split()
        if len(pred_words) == len(ref_words):
            for a, b in zip(pred_words, ref_words):
                words_total += 1
                if a == b:
                    words_ok += 1
                else:
                    diffs[(a, b)] += 1
        else:
            words_total += max(len(pred_words), len(ref_words))
            diffs[("<token-count-mismatch>", "")] += 1
    return sentences_ok, len(gold), words_ok, words_total, diffs


def classify(diffs):
    """Group word differences by the subsystem that explains them."""
    classes = Counter()
    for (a, b), n in diffs.items():
        if a == "<token-count-mismatch>":
            classes["token count (normalisation)"] += n
        elif a.replace("^", "") == b.replace("^", ""):
            classes["tonicity (stress mark)"] += n
        elif a.lower() == b.lower():
            classes["timbre or sandhi (letter case)"] += n
        else:
            classes["segmental"] += n
    return classes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--binary-fixed", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    sentences = [line.strip() for line in
                 args.corpus.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.limit:
        sentences = sentences[:args.limit]

    report = {"corpus": str(args.corpus), "sentences": len(sentences)}
    cache = {}

    binaries = [("upstream", args.binary)]
    if args.binary_fixed:
        binaries.append(("fixed", args.binary_fixed))

    for label, binary in binaries:
        for mode in range(4):
            tra = mode + 1
            strip = (mode == 3)
            gold = [normalise(x, strip) for x in run_binary(binary, sentences, mode)]
            cache[(label, mode)] = gold
            pred = [normalise(phonemize(s, tra=tra), strip) for s in sentences]
            s_ok, s_total, w_ok, w_total, diffs = score(pred, gold)
            report[f"{label}/-t{mode}"] = {
                "tra": tra,
                "sentences": f"{s_ok}/{s_total}",
                "sentence_pct": round(100 * s_ok / s_total, 2),
                "words": f"{w_ok}/{w_total}",
                "word_pct": round(100 * w_ok / w_total, 2),
                "diff_classes": dict(classify(diffs)),
                "top_diffs": [f"{a} != {b}  x{n}" for (a, b), n in diffs.most_common(30)],
            }
            print(f"{label} -t{mode} (tra={tra}): "
                  f"sentences {s_ok}/{s_total} ({100 * s_ok / s_total:.2f}%)  "
                  f"words {w_ok}/{w_total} ({100 * w_ok / w_total:.2f}%)", flush=True)

    if args.binary_fixed:
        for mode in range(4):
            upstream, fixed = cache[("upstream", mode)], cache[("fixed", mode)]
            s_ok, s_total, w_ok, w_total, diffs = score(fixed, upstream)
            report[f"fix-blast-radius/-t{mode}"] = {
                "sentences_changed": s_total - s_ok,
                "words_changed": w_total - w_ok,
                "word_pct_changed": round(100 * (w_total - w_ok) / w_total, 4),
                "top_diffs": [f"{a} != {b}  x{n}" for (a, b), n in diffs.most_common(20)],
            }
            print(f"fix blast radius -t{mode}: {s_total - s_ok}/{s_total} sentences, "
                  f"{w_total - w_ok}/{w_total} words "
                  f"({100 * (w_total - w_ok) / w_total:.3f}%)", flush=True)

    if args.json:
        args.json.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print("wrote", args.json)


if __name__ == "__main__":
    main()
