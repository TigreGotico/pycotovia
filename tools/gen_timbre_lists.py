#!/usr/bin/env python3
"""Generate pycotovia/timbre_data.py from the Cotovia C source.

The open/closed vowel timbre rules in ``trat_fon.cpp`` are driven by eight
word and termination lists.  Transcribing them by hand is error prone — the
first port of these lists swapped vowels in a dozen entries (``bébedo`` became
``bábedo``, ``oramó`` became ``oramé``) and silently changed the timbre of
every affected word.  Extract them mechanically instead.

The ``*_terminacions_*`` lists are searched with ``EN_DICCIONARIO_INVERSO``:
the C stores each entry reversed and prefix-matches it against the reversed
word, which is a suffix match.  We keep the entries exactly as the C stores
them and reverse the word at match time.

Usage:
    python3 tools/gen_timbre_lists.py /path/to/cotovia/src/cotovia/trat_fon.cpp
"""

import re
import sys
from pathlib import Path

# name in the C source -> (python name, is it searched reversed?)
LISTS = {
    "agudas_palabras_abertas": ("AGUDAS_PALABRAS_ABERTAS", False),
    "agudas_terminacions_abertas": ("AGUDAS_TERMINACIONS_ABERTAS", True),
    "graves_palabras_abertas": ("GRAVES_PALABRAS_ABERTAS", False),
    "graves_palabras_pechadas": ("GRAVES_PALABRAS_PECHADAS", False),
    "graves_terminacions_abertas": ("GRAVES_TERMINACIONS_ABERTAS", True),
    "graves_terminacions_pechadas": ("GRAVES_TERMINACIONS_PECHADAS", True),
    "esdr_terminacions_pechadas": ("ESDR_TERMINACIONS_PECHADAS", True),
    "esdr_palabras_pechadas": ("ESDR_PALABRAS_PECHADAS", False),
}


def extract(raw: bytes, name: str) -> list[str]:
    """Pull one string array out of the C source.

    The file is mostly Latin-1 but a few entries were saved as UTF-8, so each
    string is decoded independently with a Latin-1 fallback.
    """
    start = raw.find((name + "[]").encode())
    if start < 0:
        start = raw.find(name.encode())
    if start < 0:
        raise SystemExit(f"list {name!r} not found")
    end = raw.find(b"}", start)
    out = []
    for item in re.findall(rb'"([^"]*)"', raw[start:end]):
        if not item:
            continue
        try:
            out.append(item.decode("utf-8"))
        except UnicodeDecodeError:
            out.append(item.decode("latin-1"))
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    raw = Path(sys.argv[1]).read_bytes()

    lines = [
        '"""Vowel timbre word lists — GENERATED, do not edit by hand.',
        "",
        "Source: Cotovia ``src/cotovia/trat_fon.cpp``.",
        "Regenerate with ``python3 tools/gen_timbre_lists.py <cotovia>/src/cotovia/trat_fon.cpp``.",
        "",
        "Entries in the ``*_TERMINACIONS_*`` lists are stored reversed, exactly as",
        "the C stores them: they are prefix-matched against the reversed word.",
        '"""',
        "",
    ]
    for c_name, (py_name, reversed_) in LISTS.items():
        entries = extract(raw, c_name)
        note = "  # reversed entries" if reversed_ else ""
        lines.append(f"{py_name}: tuple[str, ...] = ({note}")
        for e in entries:
            lines.append(f"    {e!r},")
        lines.append(")")
        lines.append("")
        print(f"{c_name}: {len(entries)} entries")

    dest = Path(__file__).resolve().parent.parent / "pycotovia" / "timbre_data.py"
    dest.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
