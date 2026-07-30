# Parity verification

We verify pycotovia against the Cotovia C binary by running the same words through both systems and comparing the output phoneme strings.

## Test method

1. Build the Cotovia binary from source (`cotovia-mirror/src/cotovia/`).
2. Run the binary in `-St0lgl` mode (Galician, phonemes only, no stress markers).
3. Run the same words through `pycotovia.phonemize(word, lang="gl")`.
4. Compare character-by-character.

## Test corpus

The test corpus covers:
- Simple vowels and consonants
- Diphthongs and triphthongs
- The `gu` + vowel family (`guerra`, `guante`, `guia`, `guion`, `bui`, `fui`, `cuido`, `quilo`, `seguir`)
- Words ending in `-s`, `-n`, and vowels
- Words with orthographic accents (`cafe`, `publico`, `politica`)
- Exception words (`x` → `ks`/`S`, `w` → `gu`/`u`)
- Common function words

Total: **93 words**.

## Results

**90 pass, 3 deliberate mismatches.**

### Passing (90 words)

Examples: `casa`, `cantar`, `canon`, `guerra`, `guante`, `guapo`, `quilo`, `seguir`, `pais`, `maiz`, `cafe`, `europa`, `audio`, `buey`, `miel`, `bien`, `viento`, `ciencia`, `hola`, `gracias`, `que`, `quien`, `aun`, `aunque` …

### Deliberate mismatches (3 words)

These are the result of a **bug in the Cotovia C source** that we choose not to replicate.

| Word | pycotovia (correct) | Cotovia binary (bug) | Cause |
|------|---------------------|----------------------|-------|
| `bui` | `buj` | `bwi` | C `aguda()` / `grave()` has a precedence bug: `(*p-2)=='g'` is parsed as `(*p)-2=='g'`. When `*p == 'i'`, `(*p)-2` equals 103 = `'g'`, so the guard is always true and stress never shifts back to `u`. |
| `fui` | `fuj` | `fwi` | Same bug. |
| `cuido` | `kujDo` | `kwiDo` | Same bug. |

In all three cases, the correct Galician stress rule should shift stress from the final `i` to the preceding `u` when `ui` is a rising diphthong. The C source intends to guard this with `q`/`g` (for `qu`/`gu` sequences), but the precedence bug makes the guard always fire for `i`, preventing the shift.

## Why not replicate the bug?

The bug is a genuine C precedence error (`*p-2` vs `*(p-2)`). Replicating it would make pycotovia silently wrong for a well-defined class of Galician words. We document the divergence instead.

## Running the parity test

```bash
cd pycotovia
python3 tests/test_parity.py
```

This requires the Cotovia binary to be built at `../cotovia-mirror/bin/cotovia`. If the binary is missing, the test skips.

---
[← Limitations](limitations.md) · [Home](../README.md) · [API →](api.md)
