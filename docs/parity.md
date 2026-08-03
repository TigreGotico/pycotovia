# Parity verification

We verify pycotovia against the Cotovia C binary. The binary is the oracle: we run the same input through both and compare the output character by character. We never write an expected phoneme string by hand.

## Test method

1. Build the Cotovia binary from source (`cotovia-mirror/src/cotovia/`).
2. Run the binary and pycotovia at equivalent options.
3. Compare character by character.

pycotovia's `tra` levels are offset by one from the binary's `-t` levels:

| pycotovia | Cotovia binary | Output |
|-----------|----------------|--------|
| `tra=1` | `-t0` | Phonemes only |
| `tra=2` | `-t1` | Phonemes + stress marks |
| `tra=3` | `-t2` | Phonemes + stress + syllable separators |
| `tra=4` | `-t3` | `-t2` plus tonicity and vowel timbre |
| `tra=5` | — | Raw rule-engine output (no binary equivalent) |

Comparing across this offset is a common mistake. It makes pycotovia look badly wrong when it is not.

## Test corpus

Two corpora, both in `tests/test_parity.py`:

**Words (93).** Simple vowels and consonants; diphthongs and triphthongs; the `gu` + vowel family; words ending in `-s`, `-n` and vowels; words with orthographic accents; exception words; common function words.

**Sentences (65)** at the phoneme levels, plus **18** for the prosodic mode. Real Galician sentences, grouped by the behaviour they exercise:
- Open/closed vowel opposition (`ó`, `nós`, `vén`, `só`, `bóla`, `cómpre`) and the closed counterparts that must not open (`é`, `és`, `avó`, `café`)
- Hyphenated clitics: `-lo/-la/-los/-las` join to the verb, everything else splits
- The `x` family: terminal `-x`, `próxi-`, and the `pronuncianse_con_xe` exceptions
- Sentence separators resetting phrase-initial sandhi
- `ñ` and `ç` surviving accent stripping
- Function words, clitics and contractions in running text
- For `tra=4`: article/preposition/clitic chains, contractions, open-vowel
  minimal pairs, numerals, and mixed running text

## Results

**All 173 tests pass.** There are no deliberate divergences.

An earlier version of this document claimed three deliberate mismatches (`bui`, `fui`, `cuido`), on the grounds that a `*p-2` vs `*(p-2)` precedence bug in the C `aguda()`/`grave()` made the binary emit `bwi`/`fwi`/`kwiDo`. **The binary does not do that.** It emits `buj`, `fuj` and `kujDo`, which is what pycotovia emits. The claim was never true of the shipped binary, and `tests/test_parity.py::test_ui_diphthong_matches_binary` now pins both sides.

## Open divergences

These are real, reproduced against the binary, and not yet fixed. `tests/test_parity.py` records them in `KNOWN_DIVERGENCES` and `OPEN_DIVERGENCE_SENTENCES` so the suite fails if either side drifts.

| Input | pycotovia | Binary | Cause |
|-------|-----------|--------|-------|
| `doíalle` at `tra=3` | `Do-i^a-Ze` | `Do-i^-a-Ze` | Hiatus after a stressed `í` is not split. |
| `ao`, `aos` | `a^-o`, `a^-os` | `O^`, `O^s` | The contraction is a lexical open `O` in the binary. |
| `luxar` | `luksa^r` | `luSa^r` | `_prefix_match` scans the whole list; the C uses `comprobar_en_lista_de_inicio_de_palabras`, a binary search over a list that is not fully sorted, so some entries are unreachable. pycotovia matches entries the binary never reaches. |
| `twist`, `newton`, `wolfram` | `twi^st`, `ne^wtoN`, `Bolfra^m` | `tewi^st`, `ne^BtoN`, `bolfra^m` | `w` exception handling. The C rewrites every `w` in the word and falls back to `b`; pycotovia rewrites only the first and leaves the fallback to the rule engine. |

## The prosodic mode (`tra=4`)

`Trat_fon::atono_ou_tonico_aberto_ou_pechado_e_w_x()` drops the stress mark from atonic function words and assigns open/closed vowel timbre to nouns. The binary calls it from its main pipeline (`cotovia.cpp:2911`), and its effect is visible only in `-t3` output. `tra=4` ports that stage.

This matters downstream: the ProxectoNos Cotovia-alphabet gold transcriptions are `-t3` output. Scoring `tra=2` against that gold looks like a 47% stress error, but the binary at `-t1` scores the same way — the gap was the missing mode, not a rule defect.

Note that a copy of the same call at `transcripcion.cpp:741` *is* commented out. Reading only that copy suggests the stage is dead. It is not.

### What `tra=4` does not do

**Pause and phrase-group markers.** The binary also prints `#%pausa N%#` and `%prop N%` at `-t3`. Those come from the pause and syntagma modules, which pycotovia does not port. Strip them before comparing.

**Verb timbre.** `manexo_do_timbre_verbal()` resolves the timbre of a verb form from the conjugation tables in `verbos.txt`. pycotovia carries no verb lexicon, so verb forms fall through to the noun rules and sometimes come out open where the binary has them closed (`sabemos`, `volveron`, `chova`).

**Morphosyntactic disambiguation.** Cotovia picks a word's category with a Viterbi tagger over its dictionaries. pycotovia takes the first category the word is listed under in `palabrasFuncion.txt`. Words whose tonicity depends on context (`que`, `nin`, `onde`, `me`) can therefore come out wrong.

**Accented-vowel notation.** The binary writes the open stressed vowels as `E^` and `O^`, not `É` and `Ó` — verified at byte level. The accented form in the ProxectoNos gold is a transform their dataset pipeline applied, along with re-inserting punctuation from the source text. Neither is Cotovia output, so neither is done here.

### Measured parity at `-t3`

On the 30-sentence ProxectoNos set, against the binary with markers stripped:

- **96.4%** of words identical (297/308)
- **20/30** sentences identical end to end

Every remaining difference traces to one of the three unported pieces above.

## Running the parity test

```bash
python3 -m pytest tests/test_parity.py
```

This requires the Cotovia binary at `../cotovia-mirror/bin/cotovia`. If the binary is missing, the test skips.

---
[← Limitations](limitations.md) · [Home](../README.md) · [API →](api.md)
