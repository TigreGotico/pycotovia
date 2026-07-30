# Exception word lists

pycotovia (like the Cotovia binary) uses hardcoded exception lists for words that don't follow the regular G2P rules. This document explains each list and how to add to it.

## Why exceptions exist

A purely rule-based G2P cannot handle:

- **Etymological exceptions**: words borrowed from Greek/Latin where `x` is /ks/ instead of /ʃ/
- **Foreign loanwords**: words like "sandwich" where `w` is pronounced /gu/ or /u/
- **Proper nouns**: place names, brand names that have established pronunciation

The Cotovia authors built these lists by hand over years of TTS development. pycotovia ports them directly.

## Exception lists

### 1. X_PASA_A_KS (Galician)

Words where `x` should be pronounced /ks/ instead of /ʃ/ (the Galician default).

These are mostly Greek/Latin-derived words:

```python
X_PASA_A_KS = [
    "anex", "anorex", "apirex", "aprox", "asex", "asfix",
    "atarax", "atax", "auxo", "axes", "axila", "axio",
    "biconvex", "bisex", "boxe", "caquex", "carbox",
    "coax", "coex", "conex", "convex", "coxal",
    "desconex", "dislex", "eflux", "epistax", "ex",
    "flex", "fluxi", "galaxi", "hexa", "hexo",
    "hidroxi", "homosex", "index", "inflex", "intox",
    "laxan", "laxi", "lexem", "luxa", "marxis",
    "maxil", "mix", "monoxi", "nex", "ox",
    "paralax", "pirex", "proxene", "radiotax",
    "reflexi", "sexis", "sexo", "sext", "sexua",
    "sintax", "six", "taxat", "taxi", "toxi",
    "unisex", "vexil", ...
]
```

**Example:**
- `anex` → `ane` + `ks` + `` → `aneks` (not `aneS`)
- `conex` → `koneks` (not `koneS`)

**Note:** The exception is prefix-based. If a word starts with any of these prefixes, the `x` is replaced with `ks`.

### 2. PRONUNCIANSE_CON_XE (Galician)

Words where `x` should be pronounced as in "xe" (the Galician default /ʃ/), NOT as /ks/. This is the **inverse** of the above list.

These are words that might look like they should be in X_PASA_A_KS but are not:

```python
PRONUNCIANSE_CON_XE = [
    "complexo", "exacu", "execu", "exem", "exerc",
    "exip", "oxalá", "oxiv", "saxit", "saxon",
    "xerogl", "xeron", "xeros",
]
```

**Example:**
- `complexo` → `complexo` (x stays x, becomes /ʃ/)
- `exacu` → `exacu` (x stays x, becomes /ʃ/)

### 3. W_PRONUNCIASE_GU (Spanish/Galician)

Foreign loanwords where `w` is pronounced /gu/ or /gw/:

```python
W_PRONUNCIASE_GU = [
    "darwi", "hawa", "sandwi", "taiwa",
    "walk", "wash", "whisk", "winch", "wind",
]
```

**Example:**
- `sandwich` → `sand` + `gu` + `ich` → `sandguich` → `sandGitS` (Spanish) / `sandGuic` (Galician)
- `hawa` → `hagua` → `agua` (after rules)

### 4. W_PRONUNCIASE_U (Spanish/Galician)

Foreign loanwords where `w` is pronounced /u/:

```python
W_PRONUNCIASE_U = [
    "twist", "newto",
]
```

**Example:**
- `twist` → `t` + `u` + `ist` → `tuist` → `twist` (after rules)
- `newto` → `ne` + `u` + `to` → `neuto` → `newto` (after rules)

### 5. Spanish X → KS (implicit)

For Spanish (`lang="es"`), ALL words with `x` are pronounced /ks/ by default, except those in PRONUNCIANSE_CON_XE. The exception list is much simpler:

```python
# In Spanish mode:
if 'x' in word_lower:
    idx = word_lower.index('x')
    return word[:idx] + "ks" + word[idx + 1:]
```

**Example:**
- `México` (Spanish) → `méksico` → `meksiko` (after rules)
- `México` (Galician) → `méxico` → `meSiko` (after rules, x → /ʃ/)

## How exceptions are processed

The pipeline is:

1. **Lowercase** the word
2. **Check `trata_excepcions_xe`** (language-specific x handling)
3. **Check `trata_excepcions_w`** (w handling)
4. Proceed to syllabification

If an exception matches, the word is modified BEFORE syllabification. If no exception matches, the word goes through unchanged.

## Adding new exceptions

To add a new exception:

1. Identify which list it belongs to (X, W, or a new list)
2. Add the prefix to the appropriate list in `pycotovia/exceptions.py`
3. Add a test case in `tests/test_phonemize.py`
4. Run `pytest tests/test_phonemize.py` to verify

### Example: adding a new X exception

```python
# In exceptions.py:
X_PASA_A_KS = [
    # ... existing entries ...
    "maxilo",  # new entry
]
```

```python
# In tests/test_phonemize.py:
def test_maxilo_exception(self):
    self.assertEqual(phonemize("maxilo", lang="gl").strip(), "maksilo")
```

### Important notes

- **Prefix matching**: The exception lists use prefix matching. Adding "maxilo" will also match "maxilofacial".
- **Order matters**: PRONUNCIANSE_CON_XE is checked BEFORE X_PASA_A_KS. If a word is in both lists, it will use the XE pronunciation.
- **Language-specific**: X_PASA_A_KS is only used in Galician mode. Spanish mode uses a blanket `x` → `ks` rule.

## Limitations of exceptions

- **Not exhaustive**: The lists cover common words but not all possible words.
- **No ML**: The system cannot learn new exceptions from data.
- **Prefix only**: The matching is by prefix, not by full word or by suffix.
- **No context**: A word is matched the same way regardless of sentence context.

## See also

- `docs/phonetics.md`: phonetics background
- `docs/algorithm.md`: full algorithm walkthrough
- `docs/phonemes.md`: phoneme inventory
- `docs/limitations.md`: what the system does not do

---
[← Phonemes](phonemes.md) · [Home](../README.md) · [Limitations →](limitations.md)
