# Parity with the Cotovia binary

This document states what pycotovia reproduces, what it does not, and by how
much. Every number comes from `tools/parity_harness.py`. There is no claim of
"full parity" anywhere in this repository, because full parity does not exist
today.

Audit date: 2026-08-03. Corpus: 5000 Galician Wikipedia sentences
(48024 word tokens), plus the 33 ProxectoNos test sentences.

## Scope: pycotovia is a G2P, not a synthesiser

Cotovia is a full text-to-speech system. pycotovia ports the part that turns
text into a phoneme string, and stops there.

The boundary is a single line in `cotovia.cpp`. `procesado_linguistico()` and
the first half of `generacion_prosodia()` produce the phonetic sentence.
`prosodia.xerar_prosodia()` at `cotovia.cpp:2930` starts the acoustic side:
F0 contours, durations, energy, unit selection and waveform assembly. Nothing
from that line onward is in scope, and nothing from it can change the phoneme
string.

## The oracle

The oracle is the binary built from an **unmodified** `cotovia-mirror`
checkout. This matters. Earlier parity work in this repository was measured
against a local checkout that had been patched in place with the fix from
`cotovia-mirror` PR #2, and the resulting numbers and conclusions were wrong:
an earlier version of this file said "the binary emits `buj`" and "there are
no deliberate divergences". The upstream binary emits `bwi^`, and there are
two deliberate divergences. Build the oracle from a clean checkout.

pycotovia's `tra` levels equal the binary's internal `opciones.tra`, which is
one more than the `-t` flag on the command line:

| pycotovia | Binary flag | Output |
|-----------|-------------|--------|
| `tra=1` | `-t0` | Phonemes |
| `tra=2` | `-t1` | + stress marks |
| `tra=3` | `-t2` | + syllable separators |
| `tra=4` | `-t3` | + tonicity and open-vowel timbre (binary also prints pause markers) |
| `tra=5` | — | Raw rule-engine output, for debugging |

Comparing across the offset is a common mistake and makes pycotovia look far
worse than it is.

## Measured parity

Sentence agreement is exact string equality. Word agreement is token by token
over sentences whose token counts match; a token-count mismatch counts every
token of that sentence as wrong. At `tra=4` the binary's `#%pausa N%#` and
`%prop N%` markers are stripped from both sides before comparison, because
pycotovia does not emit them.

**5000 Galician Wikipedia sentences, against the upstream binary:**

| Mode | Words | Sentences |
|------|-------|-----------|
| `tra=1` / `-t0` | 95.03% (45639/48024) | 76.80% (3840/5000) |
| `tra=2` / `-t1` | 94.80% (45525/48024) | 75.38% (3769/5000) |
| `tra=3` / `-t2` | 94.45% (45357/48024) | 72.88% (3644/5000) |
| `tra=4` / `-t3` | 84.55% (40594/48013) | 56.78% (2839/5000) |

**33 ProxectoNos test sentences, against the upstream binary:**

| Mode | Words | Sentences |
|------|-------|-----------|
| `tra=1` / `-t0` | 99.45% (359/361) | 93.94% (31/33) |
| `tra=2` / `-t1` | 99.45% (359/361) | 93.94% (31/33) |
| `tra=3` / `-t2` | 98.89% (357/361) | 87.88% (29/33) |
| `tra=4` / `-t3` | 93.35% (337/361) | 63.64% (21/33) |

The ProxectoNos figures are much higher than the Wikipedia figures because
those 33 sentences are short, clean and free of abbreviations. Wikipedia text
is the honest measure.

The curated corpora in `tests/test_parity.py` pass at 100%, but they were
written against known behaviour and cannot be read as a parity measurement.
They are regression guards, not evidence.

## Why `tra=1..3` is easier than `tra=4`

At `-t0`, `-t1` and `-t2` the binary runs a short pipeline and returns before
the hard part. `procesado_linguistico()` calls, in order: `tokenizar`,
`clasificar_palabras`, `preprocesa`, `silabificar_e_acentuar`,
`transcripcion.transcribe` and `vuelca_transcripcion`, and then returns when
`tra < 4`. The morphological analyser, the Viterbi category tagger, the
syntagma module, the pause model and `trat_fon` never run.

At `-t3` all of them run. That is the whole difference between the two groups
of numbers above.

## Feature matrix

Status values:

* **PORTED-VERIFIED** — ported, and the corpus numbers above cover it.
* **PORTED-PARTIAL** — ported, with named gaps.
* **NOT-PORTED** — absent.
* **DIVERGENCE** — deliberately different from the binary; see below.
* **OUT-OF-SCOPE** — after the G2P boundary.

| C module / stage | Runs at | pycotovia | Status |
|---|---|---|---|
| `sep_pal.cpp` — `tokenizar` | all | `Phonemizer._tokenize` | PORTED-PARTIAL: hyphen and clitic handling ported; the flex/bison input markup grammar (`lex.yy.cpp`, `variantes.tab.cpp`) is not |
| `clas_pal.cpp` — `clasificar_palabras` | all | implicit | PORTED-PARTIAL: punctuation and letter classes only; no numeral, date, Roman-numeral or acronym classes |
| `preproc.cpp` — `preprocesa` | all | — | NOT-PORTED |
| `xen_nun.cpp` — numbers to words | all, through `preprocesa` | — | NOT-PORTED |
| `gbm_abreviaturas.cpp` — abbreviation expansion | all, through `preprocesa` | — | NOT-PORTED |
| `leer_frase.cpp` — sentence reading and splitting | all | `_split_sentences` | PORTED-PARTIAL: splits on `.:;` only |
| `sil_acen.cpp` — `silabificar` | all | `syllabify.py` | PORTED-PARTIAL: vowel-sequence handling differs |
| `sil_acen.cpp` — `acentuar_prosodicamente`, `aguda`, `grave` | all | `stress.py` | PORTED-VERIFIED, with one DIVERGENCE (PR #2) |
| `sil_acen.cpp` — `diacritico_dif_aberta_pechada` | all | `stress.diacritico_dif_aberta_pechada` | DIVERGENCE (PR #4) |
| `trat_fon.cpp` — `tratamento_das_excepcions_da_xe` | all | `exceptions.trata_excepcions_xe` | PORTED-PARTIAL: the list lookup is a full scan, not the binary's binary search |
| `trat_fon.cpp` — `tratamento_das_excepcions_da_w` | all | `exceptions.trata_excepcions_w` | PORTED-PARTIAL: rewrites the first `w` only; the C rewrites all of them and falls back to `b` |
| `transcripcion.cpp` — rule tables and `transcribe` | all | `engine.py`, `rules_data.py` | PORTED-VERIFIED |
| `transcripcion.cpp` — `sacar_transcripcion` output filter | all | `_strip_t0` | PORTED-VERIFIED |
| `transcripcion.cpp` — `transformar_a_alofonos` | `tra=4` | `engine.py`, same tables | PORTED-PARTIAL: the comment-preserving and intonation-break wrapper is not ported |
| `alofonos.cpp` — `crea_cadena_rupturas`, comment handling | `tra=4` | — | NOT-PORTED |
| `morfolo.cpp` — `analise_morfoloxica` | `tra=4` | — | NOT-PORTED |
| `analisis_morfosintactico.cpp`, `Viterbi_categorias.cpp`, `modelo_lenguaje.cpp` | `tra=4` | first-entry lookup in `function_words.py` | NOT-PORTED for the tagger; the lexicon is ported |
| `verbos.cpp`, `timbre.cpp` — `manexo_do_timbre_verbal` and `verbos.txt` | `tra=4` | — | NOT-PORTED |
| `trat_fon.cpp` — `atono_ou_tonico_aberto_ou_pechado_e_w_x` | `tra=4` | `prosody.py`, `tonicity.py`, `timbre.py` | PORTED-PARTIAL: noun timbre and function-word tonicity ported; verb timbre is not |
| `trat_fon.cpp` — `tonica` | `tra=4` | `tonicity.py` | PORTED-PARTIAL: needs the missing tagger for its category input |
| `sintagma.cpp` — `analise_sintagmatico` | `tra=4` | — | NOT-PORTED |
| `pausas.cpp` — `crea_frase_pausas`, `poner_pausas` | `tra=4` | — | NOT-PORTED |
| `trat_fon.cpp` — `insertar_pausa_entre_palabras`, `insertar_tipo_de_proposicion`, `asignar_pausa_entre_frases` | `tra=4` | — | NOT-PORTED |
| `rupturas_entonativas.cpp`, `minor_phrasing.cpp`, `modulo_minor_phrasing.cpp`, `viterbi_mP.cpp` | `tra=4` | — | NOT-PORTED |
| `alternativas.cpp` — alternative transcriptions (`-A`) | `-A` | — | NOT-PORTED |
| `cotovia2eagles.cpp`, `info_estructuras.cpp` — linguistic analysis output (`-L`) | `-L` | — | OUT-OF-SCOPE |
| `prosodia.cpp`, `modelo_duracion.cpp`, `frecuencia.cpp`, `energia.cpp`, `red_neuronal.cpp`, `util_neuronal.cpp`, `grupos_acentuales.cpp`, `Viterbi_acentual.cpp` | after `xerar_prosodia` | — | OUT-OF-SCOPE |
| `seleccion_unidades.cpp`, `descriptor.cpp`, `crea_descriptores.cpp`, `distancia_espectral.cpp`, `procesado_senhal.cpp`, `audio.cpp`, `locutor.cpp`, `cache.cpp`, `indices.cpp`, `matriz.cpp`, `estadistica.cpp` | synthesis | — | OUT-OF-SCOPE |
| `letras.cpp`, `utilidades.cpp`, `perfhash.cpp`, `path_list.cpp`, `gestor_busquedas_memoria.cpp`, `configuracion.cpp`, `options.cpp`, `interfaz_ficheros.cpp` | support | `charset.py`, `lookup.py` | PORTED-PARTIAL, as needed |

## Deliberate divergences

The binary is the oracle, except where an upstream defect is uncontroversial.
Those are fixed here and documented by a reference-only pull request against
`TigreGotico/cotovia-mirror`, which is never merged.

### 1. Operator precedence in `aguda()` and `grave()`

`sil_acen.cpp:434` and `sil_acen.cpp:453`:

```c
if (!((*(p-1)=='u') && p>palabra+1 && ( (*p-2)=='q' || (*p-2)=='g' ) ))
```

`*p-2` is `(*p)-2`, not `*(p-2)`. When `*p` is `'i'` (0x69), `(*p)-2` is 0x67,
which is `'g'`. The guard is therefore always true for every `i`, the stress
never shifts back, and rising `ui` diphthongs come out wrong. The comparison
is syntactically valid and semantically meaningless: it compares the result of
character arithmetic against a letter. The same line reads `*(p-1)` correctly.

* Upstream: `bui` → `bwi^`, `fui` → `fwi^`, `cuido` → `kwi^Do`
* pycotovia: `bu^j`, `fu^j`, `ku^jDo`
* Blast radius: 19 of 48024 words (0.04%), 17 of 5000 sentences
* Reference PR: [cotovia-mirror #2](https://github.com/TigreGotico/cotovia-mirror/pull/2)

### 2. Off-by-one in `diacritico_dif_aberta_pechada()`

`sil_acen.cpp:535`:

```c
cont=0;
while (*diacriticos_oposicion_aberta_pechada[cont++]!=0 ){
   if (strcmp(diacriticos_oposicion_aberta_pechada[cont],pal_entrada)==0){
```

`cont++` is in the loop guard, so the guard tests entry N and the body
compares entry N+1. Entry 0 is `"é"` and is never compared. The `"\0"`
terminator is compared instead, and can never match. The list is a table of
words whose graphic accent marks an open/closed opposition rather than stress.
`"é"`, the third person of *ser*, is the paradigm case and the reason the
table exists. Losing exactly the first element while gaining a comparison
against the terminator is the signature of the `cont++` placement, not a
design.

Verified against the binary: `"ó"` (entry 1) and `"só"` (entry 20) both match;
`"é"` (entry 0) does not.

* Upstream at `-t0..-t2`: `é` → `e^`, closed
* pycotovia at `tra=1..3`: `é` → `E^`, open
* Reference PR: [cotovia-mirror #4](https://github.com/TigreGotico/cotovia-mirror/pull/4)

**The blast radius is large, so read this before you rely on `tra=1..3`.** The
word `é` occurs 508 times in the 5000-sentence corpus. Taking the fix costs
1.04% of words and 9.2% of sentences at `tra=1..3` when measured against the
upstream binary:

| Mode | Words, with the fix | Words, replicating the bug |
|------|---------------------|----------------------------|
| `tra=1` | 95.03% | 96.07% |
| `tra=2` | 94.80% | 95.84% |
| `tra=3` | 94.45% | 95.49% |
| `tra=4` | 84.55% | 84.55% |

`tra=4` does not change. At `-t3` the prosodic stage opens `é` to `E^` anyway,
so the mode that the Cotovia-alphabet voices were trained on gives the same
string either way. That is why the fix is taken: it costs nothing downstream
and it removes a defect from the phoneme-only modes.

If you need bug-compatible `tra=1..3` output, remove `"é"` from
`DIACRITICOS_OPOSICION` in `pycotovia/stress.py`.

## Replicated quirks, not fixed

These are arguable, so the binary wins and pycotovia must match it.

**Binary search over a partly unsorted list.**
`comprobar_en_lista_de_inicio_de_palabras()` in `trat_fon.cpp:1082` is a
documented, deliberate design: a binary search, then a backward linear scan.
Its precondition is a sorted list. Three of the 118 entries of `x_pasa_a_ks`
break the byte order (`laxi`/`laxa`, `léxic`/`lux`, `máxim`/`mitilotox`), and
one of the two entries of `w_pronunciase_u` does (`twist`/`newto`). Entries
after a break can become unreachable. The defect is in the data, not in the
algorithm, and whether the unreachable entries were meant to apply cannot be
known from the source. pycotovia uses a full scan, so it reaches entries that
the binary never does. That is an accidental divergence and a gap to close,
not a fix to keep:

| Input | pycotovia | Upstream |
|-------|-----------|----------|
| `luxar` | `luksa^r` | `luSa^r` |
| `newton` | `ne^wtoN` | `ne^BtoN` |
| `wolfram` | `Bolfra^m` | `bolfra^m` |
| `twist` | `twi^st` | `tewi^st` |

## Where the remaining gap is

Every differing token at `tra=4` over the 5000-sentence corpus, grouped by
cause:

| Class | Count | Cause |
|-------|-------|-------|
| Letter case on `d`, `b`, `g` | 420 | Pause markers. The binary's `#%pausa%#` puts the next word in phrase-initial position, so the stop stays occlusive. pycotovia has no pause model, so the rule engine makes it fricative. |
| Tonicity (`^`) | 603 | The Viterbi category tagger. `sobre`, `onde`, `segundo`, `contra`, `baixo`, `un`, `e` and `i` change tonicity with their category. |
| Letter case on `e`, `o` | 477 | Vowel timbre, mostly verb forms: `foron`, `temas`, `lemos`, `teñen`. `manexo_do_timbre_verbal()` and `verbos.txt` are not ported. |
| Segmental | 812 | Mostly the `ao`/`aos` contraction (209). The rest is syllabification of vowel sequences (`maior`, `muíños`, `incluíndo`, `saíu`) and the exception-list lookup. |
| Token count | 448 sentences | Text normalisation: abbreviations (`vol.` → `volume`, `páx.` → `páxina`, `r/` → `rúa`), acronyms spelled letter by letter (`NBA` → `ene be a`), and numerals. |

Pause markers therefore change the phoneme string. They are not cosmetic.

## Reproducing these numbers

```bash
# Oracle: a clean checkout, with no local patches.
git clone https://github.com/TigreGotico/cotovia-mirror
make -C cotovia-mirror/src/cotovia

python3 tools/parity_harness.py corpus.txt \
    --binary cotovia-mirror/bin/cotovia \
    --json report.json
```

The corpus is plain text, one sentence per line, with no sentence-final
punctuation. The harness adds it. Give the binary one sentence per process:
piping many lines in at once makes it merge some of them.

The in-repo regression suite runs separately and needs the binary at
`../cotovia-mirror/bin/cotovia`:

```bash
python3 -m pytest tests/test_parity.py
```

---
[← Limitations](limitations.md) · [Home](../README.md) · [API →](api.md)
