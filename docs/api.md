# API reference

## `pycotovia.phonemize(text, lang="gl", tra=1, alphabet="cotovia")`

Convert plain text to a phoneme string.

**Parameters:**
- `text` (str): input text (Latin-1 or Unicode)
- `lang` (str): `"gl"` for Galician, `"es"` for Spanish
- `tra` (int): output level:
  - `1` = phonemes only (default)
  - `2` = phonemes + stress markers (`^`)
  - `3` = phonemes + stress + syllable separators (`-`)
  - `4` = raw rule-engine output (with `#` / `%` blocks)
- `alphabet` (str): output phonetic alphabet, one of `pycotovia.ALPHABETS`.
  Defaults to `"cotovia"` (native notation, no behavior change from prior
  releases). Any other value converts the native output through
  [scriptconv](https://github.com/TigreGotico/scriptconv). Only valid with
  `tra=1` — raises `AlphabetError` otherwise.

**Returns:** `str`: phoneme string in Cotovia notation, or the requested `alphabet`.

**Raises:**
- `AlphabetError`: unknown `alphabet` value, or `alphabet` requested with `tra != 1`
- `UnmappedSymbolError`: a phoneme has no mapping to the requested `alphabet`

**Examples:**
```python
import pycotovia

pycotovia.phonemize("guerra", lang="gl")        # "gerra"
pycotovia.phonemize("guerra", lang="gl", tra=2)   # "g^erra"
pycotovia.phonemize("guerra", lang="gl", tra=3)   # "g^e-rra"
pycotovia.phonemize("guerra", lang="gl", alphabet="ipa")       # "ɡera "
pycotovia.phonemize("cantar", lang="gl", alphabet="x-sampa")   # "kanta4 "
```

## `pycotovia.Phonemizer`

Class-based interface for repeated phonemization.

```python
from pycotovia import Phonemizer

p = Phonemizer(lang="gl")
for word in ["casa", "cantar", "guerra"]:
    print(p.phonemize(word))
```

## `pycotovia.cotovia_to_ipa(text)`

Map a Cotovia phoneme string to IPA symbols.

```python
from pycotovia import cotovia_to_ipa

cotovia_to_ipa("gerra")   # "ɣɛra"
cotovia_to_ipa("kasa")    # "kasa"
```

## `pycotovia.COTOVIA2IPA`

The raw mapping dict from Cotovia phoneme symbols to IPA strings.

## `pycotovia.ALPHABETS`

Tuple of alphabet identifiers accepted by the `alphabet` argument, enumerated
from scriptconv's convention registry (`"cotovia"`, `"ipa"`, `"x-sampa"`,
`"arpa"`, `"lexique"`, `"kirshenbaum"`, `"rfe"`).

## CLI

```bash
pycotovia [-l gl|es] [-a alphabet] < input.txt > output.txt
```

## Internal modules

These are not part of the public API but are documented for contributors:

- `pycotovia.syllabify.syllabify(word)`: syllabify a single word
- `pycotovia.stress.assign_stress(syllabified, lang)`: place stress marker
- `pycotovia.engine.apply_rules(text, rules)`: run the rule engine
- `pycotovia.charset.vocal(c)`, `consonante(c)`: Latin-1 char classification
- `pycotovia.exceptions.trata_excepcions_xe(word, lang)`, `trata_excepcions_w(word)`: exception preprocessing

## `extract_rules.py`

Build script that regenerates `rules_data.py` from the Cotovia C++ headers. Not needed at runtime.

```bash
python extract_rules.py /path/to/cotovia/src/cotovia/include/alof_gal.hpp gl > pycotovia/rules_data.py
```

---
[← Parity](parity.md) · [Home](../README.md)
