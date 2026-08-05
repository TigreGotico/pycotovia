# Phonetics for non-speakers

This guide explains the Galician and Spanish phonetics concepts you need to understand the code, even if you don't speak either language.

## The basics

Galician and Spanish are closely related Romance languages (both evolved from Latin). They share the same vowel system and most consonants. The key differences are in a few consonants and in how `x` is pronounced.

## Vowels

Both languages have five pure vowels:

| Letter | IPA | English approximation | Example |
|--------|-----|----------------------|---------|
| a | /a/ | father | casa |
| e | /e/ | met (or bet) | mesa |
| i | /i/ | feet | sí |
| o | /o/ | boat (or caught) | ola |
| u | /u/ | boot | uno |

Galician additionally distinguishes **open** vs **closed** e and o in stressed syllables (the binary can mark this, but pycotovia does not apply it in transcription mode: this is intentional).

## Diphthongs

A diphthong is two vowels pronounced as a single syllable. In Galician/Spanish:

- **Falling diphthongs** (strong → weak): `ai`, `ei`, `oi`, `au`, `eu`, `ou`, `ia`, `ie`, `io`, `ua`, `ue`, `uo`
- **Rising diphthongs** (weak → strong): `ui`, `iu`, `ai` (wait), `ei` (wait)

The "weak" vowels are **i** and **u**. When they appear next to a "strong" vowel (a, e, o), they form a diphthong.

Key examples for the code:
- `guerra` = `gue-rra` (ue is a diphthong)
- `seguir` = `se-guir` (ui is a rising diphthong)
- `bui` = `bui` (ui is a diphthong, stress should be on `u`)

## Triphthongs

A triphthong is three vowels in one syllable: weak + strong + weak.

- `guia` = `guia` (one syllable: u-i-a)
- `guion` = `guion` (one syllable: u-i-o)
- `aéreo` = `a-é-re-o` (NOT a triphthong: the accent breaks it)

This is why the `es_triptongo()` bug matters: if `uia` is split as `gui-a`, the rules produce `gia` instead of `gja`.

## Consonants

Most consonants are the same as in English or close to it. The notable ones:

| Letter | IPA | Description | Example |
|--------|-----|-------------|---------|
| ñ | /ɲ/ | like "ny" in "canyon" | niño |
| ll | /ʎ/ | like "lli" in "million" (Galician) | llingua |
| ch | /tʃ/ | like "ch" in "church" | chico |
| r (single) | /ɾ/ | single flap of the tongue | cara |
| rr | /r/ | rolled/trilled r | perro |
| g (before e,i) | /x/ or /ɣ/ | like "h" in "loch" (Galician) | gente |
| j | /x/ | same as g before e,i | juego |
| x (Galician) | /ʃ/ | like "sh" in "ship" | xaneiro |
| x (Spanish) | /ks/ | like "x" in "box" | México |
| z (Spanish) | /θ/ | like "th" in "think" (Spain) | zapato |
| c (before e,i, Spanish) | /θ/ or /s/ | like "th" or "s" | cena |

## Stress rules (prosody)

Where does the accent fall in a word without a written accent mark? This is the core of `stress.py`.

### Spanish/Galician default rules

1. **Words ending in a vowel, n, or s** → stress falls on the **penultimate** syllable (grave/llana)
   - `ca-sa` → `ca-sa` (stress on first `a`)
   - `can-tan` → `can-tan` (stress on first `a`)
   - `can-tan-te` → `can-tan-te` (stress on `tan`)

2. **Words ending in any other consonant** → stress falls on the **last** syllable (aguda)
   - `can-tar` → `can-tar` (stress on last `a`)
   - `ca-fé` → `ca-fé` (already has accent mark)

3. **Exception: i/u in diphthongs** → if the last vowel is `i` or `u` and it's part of a diphthong, stress often shifts to the preceding vowel
   - `bui` → stress on `u` (not `i`)
   - `fui` → stress on `u` (not `i`)

4. **Words with written accent marks** → the accent mark determines stress
   - `ca-fé` → stress on `é`
   - `pú-bli-co` → stress on `ú`

### The C bug (why this matters)

In the original Cotovia C code, `aguda()` and `grave()` have an operator precedence bug:

```c
// BUG: *p-2 is parsed as (*p)-2, not *(p-2)
if (!((*(p-1)=='u') && p>palabra+1 && ( (*p-2)=='q' || (*p-2)=='g' ) ))
```

When `*p == 'i'` (ASCII 105), `(*p)-2` equals 103 which is `'g'`. So the guard is always true, and the stress shift never happens for words ending in `i`. This is why the binary says `bwi` instead of `buj`.

## Syllabification rules

This is the core of `syllabify.py`. The rules are:

1. **Consonant clusters** (bl, br, cl, cr, etc.) stay together
2. **Two consonants** between vowels → split as C-CV
3. **Three consonants** → split as CC-CV or C-CCV depending on the cluster
4. **Vowel sequences** → determine if diphthong/triphthong or hiatus

### Hiatus vs diphthong

- **Hiatus** (two separate syllables): two strong vowels together (`ae`, `ea`, `eo`, `oe`)
- **Diphthong** (one syllable): strong + weak or weak + strong

Examples:
- `pa-e-lla` = hiatus (ae)
- `fue-go` = diphthong (ue)
- `a-é-re-o` = hiatus (é breaks the sequence)

## The `q`/`gu` + vowel pattern

In both languages, `q` is always followed by `u` (silent), and `g` before `e`/`i` is also followed by silent `u`:

- `que` = /ke/ (the `u` is silent)
- `gui` = /gi/ (the `u` is silent)
- `gua` = /gwa/ (the `u` is pronounced)
- `que` = /ke/ (the `u` is silent)

This is why the `q/g` guard exists in the stress logic: when shifting stress from `i` to `u`, we must NOT shift if the `u` is silent (after `q` or `g`).

## Galician vs Spanish differences

| Feature | Galician | Spanish |
|---------|----------|---------|
| `x` | /ʃ/ (sh) | /ks/ (x) |
| `g` before e/i | /x/ (h) | /x/ (h) |
| `z` | /θ/ (th) | /θ/ or /s/ |
| `ll` | /ʎ/ (lli) | /ʝ/ (y) or /ʎ/ |
| `rr` | /r/ (rolled) | /r/ (rolled) |

## What the IPA symbols mean

See `docs/phonemes.md` for the full mapping. The most common ones:

| Cotovia | IPA | Name | Example |
|---------|-----|------|---------|
| g | /ɡ/ | voiced g | gato |
| G | /ɣ/ | fricative g | amigo |
| j | /j/ | y sound | hielo |
| w | /w/ | w sound | hueso |
| J | /ɲ/ | ny | niño |
| Z | /ʎ/ | lli | llingua |
| S | /ʃ/ | sh | xaneiro |
| tS | /tʃ/ | ch | chico |
| rr | /r/ | rolled r | perro |
| r | /ɾ/ | flap r | cara |
| B | /β/ | soft b | cabo |
| D | /ð/ | soft d | nada |
| E | /ɛ/ | open e | mesa |
| O | /ɔ/ | open o | ola |
| T | /θ/ | th | zapato |

## Reading the code

When you see `vocal()`, `consonante()`, `vocal_feble()`, `vocal_aberta()` in `charset.py`, they are implementing the concepts above:
- `vocal_feble` = weak vowels (i, u, ü): these can form diphthongs
- `vocal_aberta` = strong vowels (a, e, o, and their accented forms)
- `es_diptongo()` = checks if two vowels form a diphthong
- `es_triptongo()` = checks if three vowels form a triphthong

The `syllabify.py` module is essentially implementing the rules from "Spanish/Galician syllabification" textbooks. The `stress.py` module implements the "Real Academia Española" (RAE) and "Real Academia Galega" (RAG) stress rules.

## Further reading

- [Galician phonology (Wikipedia)](https://en.wikipedia.org/wiki/Galician_phonology)
- [Spanish phonology (Wikipedia)](https://en.wikipedia.org/wiki/Spanish_phonology)
- [RAE stress rules](https://www.rae.es/dpd/acento)
- [RAG stress rules](https://academia.gal/dicionario)

---
[← Algorithm](algorithm.md) · [Home](../README.md) · [Phonemes →](phonemes.md)
