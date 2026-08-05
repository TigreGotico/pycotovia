#!/usr/bin/env python3
"""Generate pycotovia/verb_data.py from Cotovia's verb dictionaries.

Reads `data/lang/<lang>/verbos.txt` and `data/lang/<lang>/desinencias.txt` from
a cotovia-mirror checkout and writes the two tables the verb analyser needs.

`verbos.txt` is the verb-root dictionary. One line per root::

    abrac,abracar,4,abrazar,5

The first field is the root, then one or more (infinitive, model...) groups.
A root of `0` marks the irregular verbs, whose forms carry no separable root.

`desinencias.txt` is an inverse (reversed) dictionary of verb endings. One line
per ending::

    aba,19,1,21,1,19,2,21,2,...

The first field is the ending written backwards. The rest is a flat list of
alternating tense and conjugation-model codes.

Both files load in list order, and both are searched with binary search, so the
generated tables keep the file order exactly. Reordering them would change
which entries the search can reach.

Usage::

    python3 tools/gen_verb_tables.py ../cotovia-mirror/data/lang/gl \\
        --output pycotovia/verb_data.py
"""

import argparse
from pathlib import Path

#: The C caps a root at four (infinitive, models) groups and four models each
#: (NUM_INFINITIVO, NUM_MODELOS in verbos.hpp). Anything past that is dropped
#: by the loader, so it is dropped here too.
NUM_INFINITIVO = 4
NUM_MODELOS = 4


def read_lines(path: Path) -> list[str]:
    text = path.read_bytes().decode("latin-1")
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("@"):
            continue
        out.append(line)
    return out


def parse_verbos(path: Path):
    """root -> tuple of (infinitive, (model, ...))."""
    entries = []
    for line in read_lines(path):
        fields = line.split(",")
        root, rest = fields[0], fields[1:]
        groups = []
        for field in rest:
            if field.isdigit():
                if groups and len(groups[-1][1]) < NUM_MODELOS:
                    groups[-1][1].append(int(field))
            elif len(groups) < NUM_INFINITIVO:
                groups.append((field, []))
        entries.append((root, tuple((inf, tuple(m)) for inf, m in groups)))
    return entries


def parse_desinencias(path: Path):
    """reversed ending -> flat tuple of alternating (tense, model) codes."""
    entries = []
    for line in read_lines(path):
        fields = line.split(",")
        ending, codes = fields[0], fields[1:]
        entries.append((ending, tuple(int(c) for c in codes if c.isdigit())))
    return entries


def parse_encliticos(path: Path):
    """Enclitic pronouns from verbos.cpp: (reversed_enclitic, group)."""
    import re
    raw = path.read_bytes().decode("latin-1")
    start = raw.index("pron_encliticos_gallego[]={")
    end = raw.index("};", start)
    body = raw[start:end]
    return [(m.group(1), int(m.group(2)))
            for m in re.finditer(r'\{\s*"([^"]*)"\s*,\s*(\d+)\s*\}', body)]


def parse_excepcions(path: Path):
    """Words that look like verb forms but are not, from verbos.cpp."""
    import re
    raw = path.read_bytes().decode("latin-1")
    start = raw.index("excepciones_verbos[]={")
    end = raw.index("};", start)
    return [m.group(1) for m in re.finditer(r'"([^"]+)"', raw[start:end])]


def render(name, entries, doc):
    out = [f"#: {doc}", f"{name} = ("]
    for key, value in entries:
        out.append(f"    ({key!r}, {value!r}),")
    out.append(")")
    out.append("")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_dir", type=Path,
                        help="cotovia-mirror data/lang/<lang> directory")
    parser.add_argument("--source-dir", type=Path, default=None,
                        help="cotovia-mirror src/cotovia (for the enclitic table)")
    parser.add_argument("--output", type=Path,
                        default=Path("pycotovia/verb_data.py"))
    args = parser.parse_args()

    raices = parse_verbos(args.data_dir / "verbos.txt")
    desinencias = parse_desinencias(args.data_dir / "desinencias.txt")
    src = args.source_dir or (args.data_dir.parent.parent.parent / "src" / "cotovia")
    encliticos = parse_encliticos(src / "verbos.cpp")
    excepcions = parse_excepcions(src / "verbos.cpp")

    header = f'''"""Verb dictionaries, generated from Cotovia's data files.

Do not edit by hand. Regenerate with::

    python3 tools/gen_verb_tables.py ../cotovia-mirror/data/lang/gl

File order is preserved exactly, because both tables are searched with binary
search and the order decides which entries are reachable.
"""

'''
    body = (header
            + render("RAICES_VERBAIS", raices,
                     "Verb roots: (root, ((infinitive, (model, ...)), ...)). "
                     f"{len(raices)} entries, in verbos.txt order.")
            + "\n"
            + render("DESINENCIAS", desinencias,
                     "Verb endings, reversed: (reversed_ending, "
                     "(tense, model, tense, model, ...)). "
                     f"{len(desinencias)} entries, in desinencias.txt order.")
            + "\n"
            + render("ENCLITICOS", encliticos,
                     "Enclitic pronouns, reversed: (reversed_enclitic, group). "
                     f"{len(encliticos)} entries, in pron_encliticos_gallego order.")
            + "\n#: Words that look like verb forms but are not. Port of\n"
            + "#: `excepciones_verbos[]`, searched with an exact binary search.\n"
            + "EXCEPCIONS_VERBOS = (\n"
            + "".join(f"    {w!r},\n" for w in excepcions)
            + ")\n"
            + '''
#: Roots recorded as "0" carry no separable stem; their forms are looked up
#: whole. `analizar_verbos()` reaches them through its irregular branch.
RAIZ_IRREGULAR = "0"
''')
    args.output.write_text(body, encoding="utf-8")
    print(f"{args.output}: {len(raices)} roots, {len(desinencias)} endings, "
          f"{len(encliticos)} enclitics, {len(excepcions)} exceptions")


if __name__ == "__main__":
    main()
