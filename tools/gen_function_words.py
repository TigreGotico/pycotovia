#!/usr/bin/env python3
"""Generate pycotovia/function_words.py from the Cotovia language data.

The Cotovia distribution ships ``data/lang/{gl,es}/palabrasFuncion.txt``:
one line per function word, ``word,gender,number,CAT1,CAT2,...[,lemma]``.
``&``-prefixed categories are the *discarded* ones and are skipped by the C
loader (``gbm_palabras_funcion.cpp``), so we skip them too.

Usage:
    python3 tools/gen_function_words.py /path/to/cotovia/data/lang
"""

import sys
from pathlib import Path

# Category name -> numeric code, from src/cotovia/include/tip_var.hpp.
CATEGORIES = {
    "ART_DET": 1, "CONTR_CONX_ART_DET": 2, "CONTR_PREP_ART_DET": 3,
    "CONTR_INDEF_ART_DET": 4, "ART_INDET": 5, "CONTR_PREP_ART_INDET": 6,
    "INDEF": 10, "INDEF_PRON": 11, "INDEF_DET": 12, "CONTR_PREP_INDEF": 13,
    "CONTR_PREP_INDEF_DET": 14, "CONTR_PREP_INDEF_PRON": 15,
    "DEMO": 20, "DEMO_DET": 21, "DEMO_PRON": 22, "CONTR_PREP_DEMO": 23,
    "CONTR_PREP_DEMO_DET": 24, "CONTR_PREP_DEMO_PRON": 25,
    "CONTR_DEMO_INDEF": 26, "CONTR_DEMO_INDEF_DET": 27,
    "CONTR_DEMO_INDEF_PRON": 28, "CONTR_PREP_DEMO_INDEF": 29,
    "CONTR_PREP_DEMO_INDEF_DET": 30, "CONTR_PREP_DEMO_INDEF_PRON": 31,
    "POSE": 35, "POSE_DET": 36, "POSE_PRON": 37, "POSE_DISTR": 38,
    "NUME": 40, "NUME_DET": 41, "NUME_PRON": 42, "NUME_CARDI": 43,
    "NUME_CARDI_DET": 44, "NUME_CARDI_PRON": 45, "NUME_ORDI": 46,
    "NUME_ORDI_DET": 47, "NUME_ORDI_PRON": 48, "NUME_PARTI": 49,
    "NUME_PARTI_DET": 50, "NUME_PARTI_PRON": 51, "NUME_MULTI": 52,
    "NUME_COLECT": 53,
    "PRON_PERS_TON": 60, "CONTR_PREP_PRON_PERS_TON": 61, "PRON_PERS_AT": 62,
    "PRON_PERS_AT_REFLEX": 63, "PRON_PERS_AT_ACUS": 64,
    "PRON_PERS_AT_DAT": 65, "CONTR_PRON_PERS_AT_DAT_AC": 66,
    "CONTR_PRON_PERS_AT_DAT_DAT_AC": 67, "CONTR_PRON_PERS_AT": 68,
    "INDET_PRON": 69, "PRON_CORREL": 70,
    "ADVE": 80, "ADVE_LUG": 81, "ADVE_TEMP": 82, "ADVE_CANT": 83,
    "ADVE_MODO": 84, "ADVE_AFIRM": 85, "ADVE_NEGA": 86, "ADVE_DUBI": 87,
    "ADVE_ESPECIFICADOR": 88, "ADVE_ORD": 89, "ADVE_MOD": 90,
    "ADVE_COMP": 91, "ADVE_CORREL": 92, "ADVE_DISTR": 93,
    "LOC_ADVE": 100, "LOC_ADVE_LUG": 101, "LOC_ADVE_TEMP": 102,
    "LOC_ADVE_CANTI": 103, "LOC_ADVE_MODO": 104, "LOC_ADVE_AFIR": 105,
    "LOC_ADVE_NEGA": 106, "LOC_ADVE_DUBI": 107,
    "PREP": 110, "LOC_PREP": 111, "LOC_PREP_LUG": 112, "LOC_PREP_TEMP": 113,
    "LOC_PREP_CANT": 114, "LOC_PREP_MODO": 115, "LOC_PREP_CAUS": 116,
    "LOC_PREP_CONDI": 117,
    "CONX_COOR": 120, "CONX_COOR_COPU": 121, "CONX_COOR_DISX": 122,
    "CONX_COOR_ADVERS": 123, "CONX_COOR_DISTRIB": 124,
    "CONTR_CONX_COOR_COP_ART_DET": 125,
    "CONX_SUBOR": 130, "CONX_SUBOR_PROPOR": 131, "CONX_SUBOR_FINAL": 132,
    "CONX_SUBOR_CONTRAP": 133, "CONX_SUBOR_CAUS": 134,
    "CONX_SUBOR_CONCES": 135, "CONX_SUBOR_CONSE": 136,
    "CONX_SUBOR_CONDI": 137, "CONX_SUBOR_COMPAR": 138,
    "CONX_SUBOR_LOCA": 139, "CONX_SUBOR_TEMP": 140, "CONX_SUBOR_MODAL": 141,
    "CONX_SUBOR_COMPLETIVA": 142, "CONX_SUBOR_CONTI": 143,
    "LOC_CONX": 145, "LOC_CONX_COOR_COPU": 146, "LOC_CONX_COOR_ADVERS": 147,
    "LOC_CONX_SUBOR_CAUS": 150, "LOC_CONX_SUBOR_CONCES": 151,
    "LOC_CONX_SUBOR_CONSE": 152, "LOC_CONX_SUBOR_COMPAR": 153,
    "LOC_CONX_SUBOR_CONDI": 154, "LOC_CONX_SUBOR_LOCAL": 155,
    "LOC_CONX_SUBOR_TEMP": 156, "LOC_CONX_SUBOR_MODA": 157,
    "LOC_CONX_SUBOR_CONTRAP": 158, "LOC_CONX_SUBOR_FINAL": 159,
    "LOC_CONX_SUBOR_PROPOR": 160, "LOC_CONX_SUBOR_CORREL": 161,
    "RELA": 170, "INTER": 171, "EXCLA": 172,
    "NOME": 173, "LOC_SUST": 174, "NOME_PROPIO": 175,
    "ADXECTIVO": 176, "LOC_ADXE": 177,
    "VERBO": 178, "PERIFRASE": 179, "INFINITIVO": 180, "XERUNDIO": 181,
    "PARTICIPIO": 182, "INTERX": 183, "LOC_INTERX": 184,
    "LAT": 185, "LOC_LAT": 186,
}


def parse(path: Path) -> dict[str, tuple[int, ...]]:
    out: dict[str, tuple[int, ...]] = {}
    for raw in path.read_text(encoding="latin-1").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split(",")
        word = fields[0].strip().lower()
        if not word:
            continue
        cats = []
        for f in fields[3:]:
            f = f.strip()
            if f.startswith("&"):
                continue  # discarded category, skipped by the C loader
            code = CATEGORIES.get(f)
            if code is not None:
                cats.append(code)
        if cats:
            out[word] = tuple(cats)
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    lang_dir = Path(sys.argv[1])
    tables = {
        lang: parse(lang_dir / lang / "palabrasFuncion.txt")
        for lang in ("gl", "es")
    }
    dest = Path(__file__).resolve().parent.parent / "pycotovia" / "function_words.py"
    lines = [
        '"""Function-word categories — GENERATED, do not edit by hand.',
        "",
        "Source: Cotovia ``data/lang/<lang>/palabrasFuncion.txt``.",
        "Regenerate with ``python3 tools/gen_function_words.py <cotovia>/data/lang``.",
        '"""',
        "",
    ]
    for lang, table in tables.items():
        lines.append(f"FUNCTION_WORDS_{lang.upper()}: dict[str, tuple[int, ...]] = {{")
        for word in sorted(table):
            lines.append(f"    {word!r}: {table[word]!r},")
        lines.append("}")
        lines.append("")
    lines += [
        "FUNCTION_WORDS = {",
        '    "gl": FUNCTION_WORDS_GL,',
        '    "es": FUNCTION_WORDS_ES,',
        "}",
        "",
    ]
    dest.write_text("\n".join(lines), encoding="utf-8")
    for lang, table in tables.items():
        print(f"{lang}: {len(table)} function words")
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
