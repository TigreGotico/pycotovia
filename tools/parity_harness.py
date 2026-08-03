#!/usr/bin/env python3
"""Corpus parity harness: pycotovia against the Cotovia binary at every mode.

The binary is the oracle. This tool runs a plain-text corpus (one sentence per
line) through both, at every `tra` level, and reports word-level and
sentence-level agreement. Every number in `docs/parity.md` comes from here.

There are two oracles, and both are first class. See `docs/oracles.md`.

* **fixed** (default) — upstream plus the adjudicated bug fixes, the
  reference build. Paired with pycotovia's default behaviour.
* **pristine** — stock upstream, defects included. Paired with
  `keep_bugs=True`.

Usage::

    # Score against the reference build (the headline numbers).
    python3 tools/parity_harness.py corpus.txt --fixed ../cotovia-mirror/bin/cotovia

    # Score keep_bugs=True against stock upstream.
    python3 tools/parity_harness.py corpus.txt --oracle pristine \\
        --pristine ../cotovia-pristine/bin/cotovia

    # Both, plus the exhaustive divergence table between the two builds.
    python3 tools/parity_harness.py corpus.txt --oracle both \\
        --fixed ../cotovia-mirror/bin/cotovia \\
        --pristine ../cotovia-pristine/bin/cotovia

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
    parser.add_argument("--oracle", choices=("fixed", "pristine", "both"),
                        default="fixed",
                        help="which build to score against (default: fixed)")
    parser.add_argument("--fixed", type=Path, default=Path("../cotovia-mirror/bin/cotovia"),
                        help="the reference build: upstream plus the adjudicated fixes")
    parser.add_argument("--pristine", type=Path,
                        default=Path("../cotovia-pristine/bin/cotovia"),
                        help="stock upstream, defects included")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    sentences = [line.strip() for line in
                 args.corpus.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.limit:
        sentences = sentences[:args.limit]

    report = {"corpus": str(args.corpus), "sentences": len(sentences)}
    cache = {}

    #: Each oracle is paired with the pycotovia behaviour it defines.
    #: The fixed build defines the default; the pristine build defines
    #: keep_bugs=True. Crossing the pair is meaningless.
    wanted = ("fixed", "pristine") if args.oracle == "both" else (args.oracle,)
    oracles = [(name, args.fixed if name == "fixed" else args.pristine,
                name == "pristine") for name in wanted]

    for label, binary, keep_bugs in oracles:
        if not Path(binary).exists():
            print(f"skipping {label}: no binary at {binary}")
            continue
        for mode in range(4):
            tra = mode + 1
            strip = (mode == 3)
            gold = [normalise(x, strip) for x in run_binary(binary, sentences, mode)]
            cache[(label, mode)] = gold
            pred = [normalise(phonemize(s, tra=tra, keep_bugs=keep_bugs), strip)
                    for s in sentences]
            s_ok, s_total, w_ok, w_total, diffs = score(pred, gold)
            report[f"{label}/-t{mode}"] = {
                "tra": tra,
                "keep_bugs": keep_bugs,
                "sentences": f"{s_ok}/{s_total}",
                "sentence_pct": round(100 * s_ok / s_total, 2),
                "words": f"{w_ok}/{w_total}",
                "word_pct": round(100 * w_ok / w_total, 2),
                "diff_classes": dict(classify(diffs)),
                "top_diffs": [f"{a} != {b}  x{n}" for (a, b), n in diffs.most_common(30)],
            }
            print(f"{label} (keep_bugs={keep_bugs}) -t{mode} (tra={tra}): "
                  f"sentences {s_ok}/{s_total} ({100 * s_ok / s_total:.2f}%)  "
                  f"words {w_ok}/{w_total} ({100 * w_ok / w_total:.2f}%)", flush=True)

    if args.oracle == "both":
        for mode in range(4):
            if ("fixed", mode) not in cache or ("pristine", mode) not in cache:
                continue
            pristine, fixed = cache[("pristine", mode)], cache[("fixed", mode)]
            s_ok, s_total, w_ok, w_total, diffs = score(fixed, pristine)
            report[f"oracle-divergence/-t{mode}"] = {
                "sentences_differing": s_total - s_ok,
                "words_differing": w_total - w_ok,
                "word_pct_differing": round(100 * (w_total - w_ok) / w_total, 4),
                "all_diffs": [f"{a} != {b}  x{n}" for (a, b), n in diffs.most_common()],
            }
            print(f"fixed vs pristine -t{mode}: {s_total - s_ok}/{s_total} sentences, "
                  f"{w_total - w_ok}/{w_total} words "
                  f"({100 * (w_total - w_ok) / w_total:.3f}%)", flush=True)

    if args.json:
        args.json.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print("wrote", args.json)


if __name__ == "__main__":
    main()
