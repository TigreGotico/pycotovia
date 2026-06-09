#!/usr/bin/env python3
"""
Extract phonetic rule tables from alof_gal.hpp (C source, Latin-1 encoded)
into a Python module at pycotovia/rules_data.py.

Handles #ifdef _CONSIDERA_SEMIVOCALES blocks, generating both regular and
_sv variants of each rule dict.
"""

import re
import os
import sys
from pathlib import Path


# ── dispatch key mapping — language-specific override tables ──────────
# From Transcripcion::inicializar_reglas_transcripcion() lines 566-577.

LANG_DISPATCH: dict[str, dict[int, str]] = {
    "GALEGO": {
        0x20: "regla_cadeas_iniciadas_por_espacio",
        0x6E: "regla_cadeas_iniciadas_por_n",
        0x78: "regla_cadeas_iniciadas_por_x",
        0x23: "regla_cadeas_iniciadas_por_silencio",
        0x2D: "regla_cadeas_iniciadas_por_guion",
    },
    "CASTELLANO": {
        0x20: "cast_regla_cadeas_iniciadas_por_espacio",
        0x6E: "cast_regla_cadeas_iniciadas_por_n",
        0x78: "cast_regla_cadeas_iniciadas_por_x",
        0x23: "cast_regla_cadeas_iniciadas_por_silencio",
        0x2D: "cast_regla_cadeas_iniciadas_por_guion",
    },
}

# Shared dispatch (used by both languages, lines 579-635 + ansi.hpp)
SHARED_DISPATCH: dict[int, str] = {
    0x5E: "regla_cadeas_iniciadas_por_acento_prosodico",
    0x61: "regla_cadeas_iniciadas_por_a",
    0x65: "regla_cadeas_iniciadas_por_e",
    0xE9: "regla_cadeas_iniciadas_por_e_acentuado",
    0x69: "regla_cadeas_iniciadas_por_i",
    0x6F: "regla_cadeas_iniciadas_por_o",
    0xF3: "regla_cadeas_iniciadas_por_o_acentuado",
    0x75: "regla_cadeas_iniciadas_por_u",
    0x2C: "regla_cadeas_iniciadas_por_coma",
    0x62: "regla_cadeas_iniciadas_por_b",
    0x63: "regla_cadeas_iniciadas_por_c",
    0x64: "regla_cadeas_iniciadas_por_d",
    0x66: "regla_cadeas_iniciadas_por_f",
    0x67: "regla_cadeas_iniciadas_por_g",
    0x68: "regla_cadeas_iniciadas_por_h",
    0x6A: "regla_cadeas_iniciadas_por_j",
    0x6B: "regla_cadeas_iniciadas_por_k",
    0x6C: "regla_cadeas_iniciadas_por_l",
    0x6D: "regla_cadeas_iniciadas_por_m",
    0xF1: "regla_cadeas_iniciadas_por_enne",
    0x70: "regla_cadeas_iniciadas_por_p",
    0x71: "regla_cadeas_iniciadas_por_q",
    0x72: "regla_cadeas_iniciadas_por_r",
    0x73: "regla_cadeas_iniciadas_por_s",
    0x74: "regla_cadeas_iniciadas_por_t",
    0x76: "regla_cadeas_iniciadas_por_v",
    0x77: "regla_cadeas_iniciadas_por_w",
    0x79: "regla_cadeas_iniciadas_por_y",
    0x7A: "regla_cadeas_iniciadas_por_z",
    0xFC: "regla_cadeas_iniciadas_por_u_con_dierese",
    0xEF: "regla_cadeas_iniciadas_por_i_con_dierese",
    0xEB: "regla_cadeas_iniciadas_por_e_con_dierese",
    0xE7: "regla_cadeas_iniciadas_por_cedilla",
    0x2E: "regla_cadeas_iniciadas_por_punto",
    0x3B: "regla_cadeas_iniciadas_por_punt_e_coma",
    0x3A: "regla_cadeas_iniciadas_por_dous_puntos",
    0x27: "regla_cadeas_iniciadas_por_simples_cominhas",
    0x22: "regla_cadeas_iniciadas_por_comillas_dobles",
    0xBF: "regla_cadeas_iniciadas_por_apertura_interrogacion",
    0xA1: "regla_cadeas_iniciadas_por_exclamacion_apertura",
    0x3F: "regla_cadeas_iniciadas_por_peche_interrogacion",
    0x21: "regla_cadeas_iniciadas_por_pech_exclamacion",
    0x2A: "regla_cadeas_iniciadas_por_asterisco",
    0x28: "regla_cadeas_iniciadas_por__apertura_parentese",
    0x29: "regla_cadeas_iniciadas_po_peche_parentese",
    0x85: "regla_cadeas_iniciadas_por_suspensivos",
}
# vocal_minuscula_rara maps multiple keys to the same table
_VOCAL_MINUSCULA_RARA_KEYS = [0xE0, 0xE8, 0xEC, 0xF2, 0xF9, 0xE2, 0xEA, 0xEE, 0xF4, 0xFB, 0xE4, 0xF6]
for _k in _VOCAL_MINUSCULA_RARA_KEYS:
    SHARED_DISPATCH[_k] = "regla_cadeas_iniciadas_por_vocal_minuscula_rara"


# ── helpers ────────────────────────────────────────────────────────────────

def remove_c_comments(text: str) -> str:
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    text = re.sub(r'//[^\n]*', '', text)
    return text


def unescape_c_string(s: str) -> str:
    """Convert a C string literal body (no surrounding quotes) to Python str."""
    chars: list[str] = []
    i = 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            esc = s[i + 1]
            m = {'"': '"', '\\': '\\', 'n': '\n', 't': '\t', 'r': '\r'}
            chars.append(m.get(esc, esc))
            i += 2
        else:
            chars.append(s[i])
            i += 1
    return ''.join(chars)


def split_entry_by_commas(entry: str) -> list[str]:
    """Split a C initializer like ``"a^i", 3, "a^j"`` at top-level commas."""
    parts: list[str] = []
    i = 0
    start = 0
    depth = 0
    n = len(entry)
    while i < n:
        ch = entry[i]
        if ch == '"':
            i += 1
            while i < n and entry[i] != '"':
                if entry[i] == '\\':
                    i += 1
                i += 1
        elif ch in '({[':
            depth += 1
        elif ch in ')}]':
            depth -= 1
        elif ch == ',' and depth == 0:
            parts.append(entry[start:i])
            start = i + 1
        i += 1
    if start < n:
        parts.append(entry[start:])
    return parts


def parse_table_body(body: str) -> list[tuple[str, int, str]]:
    """Parse the content *inside* the outermost ``{…}`` of a t_regla array."""
    rules: list[tuple[str, int, str]] = []
    i = 0
    n = len(body)
    while i < n:
        ch = body[i]
        if ch in ' \t\n\r,':
            i += 1
            continue
        if ch != '{':
            i += 1
            continue

        # find matching }
        depth, j = 1, i + 1
        while j < n and depth:
            c = body[j]
            if c == '"':
                j += 1
                while j < n and body[j] != '"':
                    if body[j] == '\\':
                        j += 1
                    j += 1
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
            j += 1

        entry_raw = body[i + 1: j - 1]  # between { and }
        parts = [p.strip() for p in split_entry_by_commas(entry_raw)]

        if len(parts) == 3:
            a, l, c = parts
            if a == '0' and l == '0' and c == '0':
                break
            ant = unescape_c_string(a.strip('"'))
            con = unescape_c_string(c.strip('"'))
            try:
                rules.append((ant, int(l), con))
            except ValueError:
                pass  # skip malformed

        i = j
    return rules


# ── main parser ────────────────────────────────────────────────────────────

def parse_rules_hpp(raw: bytes) -> dict[str, dict[str, list | None]]:
    text = raw.decode('latin-1')
    text = remove_c_comments(text)

    length = len(text)

    # --- Pre-scan for #ifdef / #else / #endif to annotate sv-state per position
    # sv_state[i] ∈ {None (no sv block), True (inside #ifdef), False (inside #else)}
    sv_state: list = [None] * length
    cur: bool | None = None
    i = 0
    while i < length:
        if text[i:i + 29] == '#ifdef _CONSIDERA_SEMIVOCALES':
            cur = True
            while i < length and text[i] != '\n':
                sv_state[i] = cur
                i += 1
            continue
        if text[i:i + 5] == '#else' and (i + 5 >= length or text[i + 5] in '\n\r'):
            cur = False
            while i < length and text[i] != '\n':
                sv_state[i] = cur
                i += 1
            continue
        if text[i:i + 6] == '#endif' and (i + 6 >= length or text[i + 6] in '\n\r'):
            cur = None
            while i < length and text[i] != '\n':
                i += 1
            continue
        sv_state[i] = cur
        i += 1

    # --- Extract tables
    table_pat = re.compile(r'const\s+t_regla\s+(\w+)\[\]\s*=\s*\{')
    tables: dict[str, dict[str, list | None]] = {}

    for m in table_pat.finditer(text):
        name = m.group(1)

        # locate the opening brace of the array body
        brace = text.index('{', m.start())
        body_start = brace + 1

        depth = 1
        j = body_start
        while j < length and depth:
            ch = text[j]
            if ch == '"':
                j += 1
                while j < length and text[j] != '"':
                    if text[j] == '\\':
                        j += 1
                    j += 1
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
            j += 1

        body = text[body_start: j - 1]
        rules = parse_table_body(body)

        if name not in tables:
            tables[name] = {'non_sv': None, 'sv': None}

        sv = sv_state[brace]
        if sv is True:
            tables[name]['sv'] = rules
        elif sv is False:
            tables[name]['non_sv'] = rules
        else:
            # not inside any ifdef block → both variants get the same rules
            tables[name]['non_sv'] = rules
            tables[name]['sv'] = rules

    return tables


# ── output generation ──────────────────────────────────────────────────────

def format_rules_list(rules: list[tuple[str, int, str]]) -> str:
    """Pretty-print a list of (ant, length, con) tuples for Python output."""
    lines: list[str] = ["["]
    for ant, ln, con in rules:
        ant_esc = ant.replace('\\', '\\\\').replace("'", "\\'")
        con_esc = con.replace('\\', '\\\\').replace("'", "\\'")
        lines.append(f"    ('{ant_esc}', {ln}, '{con_esc}'),")
    lines.append("]")
    return '\n'.join(lines)


def build_main_dict(variant: str, lang: str, all_tables: dict) -> dict[int, list]:
    """Build one language x variant dispatch dict."""
    result: dict[int, list] = {}

    def add_table(tbl_name: str):
        rules = all_tables[tbl_name].get(variant) or all_tables[tbl_name].get('non_sv')
        if not rules:
            return
        # look up which keys this table maps to — we need the reverse mapping
        for key, name in LANG_DISPATCH.get(lang, {}).items():
            if name == tbl_name:
                result.setdefault(key, []).extend(rules)
                return
        for key, name in SHARED_DISPATCH.items():
            if name == tbl_name:
                result.setdefault(key, []).extend(rules)

    # language-specific tables first
    for _key, tbl_name in LANG_DISPATCH.get(lang, {}).items():
        if tbl_name in all_tables:
            add_table(tbl_name)

    # then shared tables
    added_shared = set()
    for _key, tbl_name in SHARED_DISPATCH.items():
        if tbl_name in all_tables and tbl_name not in added_shared:
            add_table(tbl_name)
            added_shared.add(tbl_name)

    return dict(sorted(result.items()))


def generate_output_file(tables: dict) -> str:
    lines: list[str] = []
    lines.append('# Galician rules: {first_char_byte: [(antecedent_str, consume_len, consequent_str), ...]}')
    lines.append('')
    lines.append('# pylint: disable=line-too-long')

    for variant, suffix in [('non_sv', ''), ('sv', '_SV')]:
        for lang_name in ('GALEGO', 'CASTELLANO'):
            var_name = f'{lang_name}_RULES{suffix}'
            d = build_main_dict(variant, lang_name, tables)
            lines.append(f'{var_name}: dict[int, list[tuple[str, int, str]]] = {{')
            for key, rules in d.items():
                key_repr = f'0x{key:02X}'
                lines.append(f'    {key_repr}: {format_rules_list(rules)},')
            lines.append('}')
            lines.append('')

    return '\n'.join(lines)





# ── main ───────────────────────────────────────────────────────────────────

def main():
    script_dir = Path(__file__).resolve().parent
    hpp_path = script_dir.parent.parent / 'cotovia-mirror' / 'src' / 'cotovia' / 'include' / 'alof_gal.hpp'
    hpp_path = hpp_path.resolve()

    if not hpp_path.exists():
        print(f'ERROR: {hpp_path} not found', file=sys.stderr)
        sys.exit(1)

    raw = hpp_path.read_bytes()
    tables = parse_rules_hpp(raw)

    output_py = generate_output_file(tables)

    out_dir = script_dir / 'pycotovia'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'rules_data.py'
    out_path.write_text(output_py)

    print(f'Wrote {out_path}')

    # stats
    for name, tbl in tables.items():
        nsv = len(tbl['non_sv'] or [])
        sv  = len(tbl['sv'] or [])
        if tbl['non_sv'] == tbl['sv']:
            print(f'  {name}: {nsv} rules (one variant)')
        else:
            print(f'  {name}: {nsv} rules (no SV) / {sv} rules (SV)')


if __name__ == '__main__':
    main()
