# The algorithm

This document explains the full G2P (grapheme-to-phoneme) algorithm step-by-step, with examples. You don't need to speak Galician or Spanish to follow it.

## Overview

The pipeline has four stages:

1. **Preprocessing** — lowercase, handle exceptions, prepare the word
2. **Syllabification** — split the word into syllables
3. **Stress assignment** — find the stressed vowel and mark it
4. **Rule engine** — apply ~2,800 rewrite rules to convert letters to phonemes

## Stage 1: Preprocessing

### Lowercasing

The Cotovia binary lowercases everything before processing. We do the same:

```
"Ola" → "ola"
"México" → "méxico"
"GUERRA" → "guerra"
```

### Exception handling

Some words don't follow the regular rules. We have hardcoded lists:

- **x → ks** (Spanish): "México" → "méksico" (in Spanish mode)
- **x → S** (Galician): "xaneiro" stays "xaneiro" (the `x` becomes /ʃ/)
- **w → gu/u** (loanwords): "sandwich" → "sandguich" → "sandGitS" (Spanish), "sandwich" → "sandguich" → "sandGuic" (Galician)

These are handled by `exceptions.py` before any other processing.

## Stage 2: Syllabification

### The algorithm

The syllabifier (`syllabify.py`) scans the word left-to-right and decides where to split. The core rules are:

1. **Vowel sequences** → check if diphthong/triphthong or hiatus
2. **Consonant clusters** → check if indivisible (bl, br, etc.)
3. **Consonant count between vowels** → split C-CV or CC-CV

### Example: "guerra"

Input: `guerra`

1. Find vowels: `u`, `e`, `a`
2. Check `ue` → diphthong (weak + strong)
3. Between `e` and `a` we have `rr` → indivisible cluster
4. Result: `gue-rra`

### Example: "guia"

Input: `guia`

1. Find vowels: `u`, `i`, `a`
2. Check `uia` → triphthong (weak + strong + weak)
3. Result: `guia` (one syllable)

If we had the bug (splitting as `gui-a`), the rules would produce `gia` instead of `gja`.

### Example: "cantar"

Input: `cantar`

1. Find vowels: `a`, `a`
2. Between them: `nt` → two consonants, split as `n-tar`
3. Result: `can-tar`

### Example: "seguir"

Input: `seguir`

1. Find vowels: `e`, `u`, `i`
2. Check `ui` → diphthong (weak + strong)
3. Between `e` and `u`: `g` → single consonant, goes with next vowel
4. Result: `se-guir`

## Stage 3: Stress assignment

### The algorithm

After syllabification, we mark the stressed vowel with `^`. The rules are:

1. **Word has an accent mark** → that vowel is stressed
   - `café` → `ca-fé` (é is already marked)
   - `público` → `pú-bli-co` (ú is already marked)

2. **Word ends in a vowel, n, or s** → stress the penultimate syllable
   - `ca-sa` → `ca^-sa`
   - `can-tan` → `can-tan` (no change needed, already aguda)
   - `can-tan-te` → `can-tan-te` (stress on `tan`)

3. **Word ends in any other consonant** → stress the last syllable
   - `can-tar` → `can-tar` (already on last syllable)
   - `ca-fé` → `ca-fé` (already marked)

4. **i/u in diphthongs** → if the last vowel is `i` or `u` and part of a diphthong, stress shifts to the preceding vowel
   - `bui` → `bu^i` (stress on `u`, not `i`)
   - `fui` → `fu^i` (stress on `u`, not `i`)
   - `cui-do` → `cu^i-do` (stress on `u`, not `i`)

5. **Exception: silent u after q/g** → don't shift if the `u` is silent
   - `qui-lo` → `qui^-lo` (stress stays on `i` because `u` is silent after `q`)
   - `gue-rra` → `gue^-rra` (stress stays on `e` because `u` is silent after `g`)

### The C bug (detailed)

The original Cotovia code has a bug in the `q/g` guard:

```c
// This is what the code INTENDED:
if (!((*(p-1)=='u') && p>palabra+1 && ( *(p-2)=='q' || *(p-2)=='g' ) ))
    p--;

// This is what the code ACTUALLY does (operator precedence):
if (!((*(p-1)=='u') && p>palabra+1 && ( (*p-2)=='q' || (*p-2)=='g' ) ))
    p--;
```

In C, `*p-2` is parsed as `(*p)-2`. When `*p == 'i'` (ASCII 105), `(*p)-2` equals 103 which is `'g'`. So the guard `(q/g)` is ALWAYS true when the last vowel is `i`, meaning the shift never happens.

**Impact:**
- `bui` → binary says `bwi` (stress on `i`), correct is `buj` (stress on `u`)
- `fui` → binary says `fwi`, correct is `fuj`
- `cuido` → binary says `kwiDo`, correct is `kujDo`

**Fix:** Use `p[-2]` or `*(p-2)` instead of `*p-2`.

## Stage 4: Rule engine

### The algorithm

The rule engine (`engine.py`) is a simple longest-match-first rewrite system. It works like this:

1. Take the input string (e.g., `## gue^-rra ##`)
2. Look at the first character (`#`)
3. Find all rules that start with `#`
4. Try them in order of longest antecedent first
5. If a rule matches, replace the matched text and advance
6. If no rule matches, keep the character and advance by 1

### Example rules

```
## gue^ → # g^e    (at phrase start, gu becomes g)
## gue  → # ge     (at phrase start, gu becomes g)
    e^  → e^        (stressed e stays stressed e)
    rr  → rr        (double r stays double r)
    a # → a #       (a at end stays a)
```

### Example: "guerra"

Input: `## gue^-rra ##`

1. Position 0: `## gue^` → matches `# g^e` → output: `## g^e`
   Wait, let's trace more carefully:

Actually the rule engine processes the FULL string. The rules are:

```
"## gue^" → "# g^e"   (consume 7, output 5)
"## gue"  → "# ge"    (consume 6, output 4)
"  gue^"  → " g^e"    (consume 6, output 4)
"  gue"   → " ge"     (consume 5, output 3)
"   e^"   → " e^"     (consume 4, output 3)
"   e"    → " e"      (consume 3, output 2)
"    rr"  → " rr"     (consume 5, output 3)
"    a ##" → " a #"   (consume 6, output 4)
```

Result after all rules: `## g^e-rra ##`

Then strip `##` and `-` and `^` for `tra=1` output: `gerra`

### Example: "guia"

Input: `## guia^ ##`

1. `## guia^` → matches `# g^ja` → output: `# g^ja`
2. `a #` → matches `a #` → output: `a #`

Result: `# g^ja #`
Strip: `gja`

If the syllabifier had split it as `gui-a`:
- Input: `## gui-a^ ##`
- `## gui` → `# gi` (no `^` because stress is in second syllable)
- Result: `# gi-a #`
- Strip: `gia` ← WRONG

### Why ~2,800 rules?

The rules are generated from the C header files. They cover:
- Every letter-to-phoneme mapping
- Context-dependent rules (e.g., `g` before `e`/`i` is different)
- Stress placement
- Syllable boundaries
- Phrase boundaries (`##` and `#`)

The rules are sorted by antecedent length (longest first) to ensure the most specific rule matches first.

## Limitations

1. **No context** — each word is processed independently. "read" (past) and "read" (present) are the same.
2. **No named entities** — "Houston" is processed as if it were a regular word.
3. **No dialects** — only standard Galician and Spanish.
4. **No loanword pronunciation** — "software" is processed as Spanish/Galician rules, not English.
5. **Numbers** — written as digits ("123") are treated as non-letters and ignored.

## Further reading

- `docs/phonetics.md` — phonetics background
- `docs/architecture.md` — module map
- `docs/parity.md` — verification results
- `docs/phonemes.md` — full phoneme inventory
- `docs/exceptions.md` — exception word lists
