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

The reference is the **fixed** build: upstream `cotovia-mirror` plus the two
adjudicated bug fixes (`cotovia-mirror` PR #2 and PR #4). Every headline
number below is measured against it, and it is what pycotovia reproduces by
default.

The **pristine** build — stock upstream, defects included — is the second
oracle. `keep_bugs=True` reproduces it. Both builds and the exhaustive
divergence table between them are in [oracles.md](oracles.md).

```python
phonemize("fui cuido", tra=2)                   # fixed build, the default
phonemize("fui cuido", tra=2, keep_bugs=True)   # stock upstream binary
```

Each oracle is paired with the behaviour it defines. Scoring default
pycotovia against the pristine build, or `keep_bugs=True` against the fixed
build, measures the difference between the two binaries and nothing useful
about the port. The harness enforces the pairing.

Numbers taken before 2026-08-03 were measured against the fixed build and
remain valid as such, but the corpus and the method have changed, so they are
not comparable with the tables below. Quote the current numbers.

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

**5000 Galician Wikipedia sentences.** Default pycotovia against the fixed
build, and `keep_bugs=True` against the pristine build:

| Mode | Words (fixed) | Sentences (fixed) | Words (pristine) | Sentences (pristine) |
|------|---------------|-------------------|------------------|----------------------|
| `tra=1` / `-t0` | 96.67% (46427/48024) | 90.38% (4519/5000) | 96.68% (46429/48024) | 90.42% (4521/5000) |
| `tra=2` / `-t1` | 96.44% (46314/48024) | 88.68% (4434/5000) | 96.44% (46315/48024) | 88.70% (4435/5000) |
| `tra=3` / `-t2` | 96.09% (46147/48024) | 85.74% (4287/5000) | 96.09% (46147/48024) | 85.74% (4287/5000) |
| `tra=4` / `-t3` | 85.07% (40845/48013) | 59.40% (2970/5000) | 85.07% (40845/48013) | 59.40% (2970/5000) |

The two columns track each other to within two tokens, which is the check that
`keep_bugs` is doing its job: both modes reproduce their own oracle equally
well, so the remaining gap is the unported subsystems and not the fixes.

**33 ProxectoNos test sentences.** Identical against either oracle:

| Mode | Words | Sentences |
|------|-------|-----------|
| `tra=1` / `-t0` | 100% (361/361) | 100% (33/33) |
| `tra=2` / `-t1` | 100% (361/361) | 100% (33/33) |
| `tra=3` / `-t2` | 99.45% (359/361) | 93.94% (31/33) |
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
| `preproc.cpp` — `transformacion_de_contraccion` | all | `phonemize.CONTRACCIONS` | PORTED-VERIFIED |
| `preproc.cpp` — everything else in `preprocesa` | all | — | NOT-PORTED |
| `xen_nun.cpp` — numbers to words | all, through `preprocesa` | — | NOT-PORTED |
| `gbm_abreviaturas.cpp` — abbreviation expansion | all, through `preprocesa` | — | NOT-PORTED |
| `leer_frase.cpp` — sentence reading and splitting | all | `_split_sentences` | PORTED-PARTIAL: splits on `.:;` only |
| `sil_acen.cpp` — `silabificar` | all | `syllabify.py` | PORTED-PARTIAL: vowel-sequence handling differs |
| `sil_acen.cpp` — `acentuar_prosodicamente`, `aguda`, `grave` | all | `stress.py` | PORTED-VERIFIED, with one DIVERGENCE (PR #2) |
| `sil_acen.cpp` — `diacritico_dif_aberta_pechada` | all | `stress.diacritico_dif_aberta_pechada` | DIVERGENCE (PR #4) |
| `trat_fon.cpp` — `tratamento_das_excepcions_da_xe` | all | `exceptions.trata_excepcions_xe` | PORTED-VERIFIED |
| `trat_fon.cpp` — `tratamento_das_excepcions_da_w` | all | `exceptions.trata_excepcions_w` | PORTED-VERIFIED, except `twist` |
| `trat_fon.cpp` — `comprobar_en_lista_de_inicio_de_palabras` | all | `lookup.buscar_inicio` | PORTED-VERIFIED |
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

## The two adjudicated bug fixes

The binary is the oracle, except where an upstream defect is uncontroversial.
Those are fixed in the reference build and in pycotovia's default behaviour,
and each one is documented by a reference-only pull request against
`TigreGotico/cotovia-mirror`.

[oracles.md](oracles.md) carries the full case for each fix — the C evidence,
the proof of intent, the Galician phonology, and the exhaustive divergence
table between the two builds. In summary:

| Fix | Defect | Effect | Reference PR |
|-----|--------|--------|--------------|
| 1 | `(*p-2)` parses as `((*p)-2)` in `aguda()`/`grave()`, so the silent-`u` guard fires for every `i` | rising `ui` outside `qu`/`gu` keeps the stress on the `i`: `fwi^` instead of `fu^j` | [#2](https://github.com/TigreGotico/cotovia-mirror/pull/2) |
| 2 | `cont++` in the guard of the diacritic loop, so entry 0 (`"é"`) is never compared | `é` comes out closed at `-t0..-t2`, and open at `-t3` from the prosodic stage | [#4](https://github.com/TigreGotico/cotovia-mirror/pull/4) |

Neither fix costs anything against the reference build: by construction,
default pycotovia and the fixed binary agree on both. Against the pristine
build the two fixes account for 527 of 48024 tokens (1.097%) at `-t0..-t2` and
18 tokens (0.041%) at `-t3`. `keep_bugs=True` reproduces the pristine build,
so nothing that depends on stock output is stranded.

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

`lookup.buscar_inicio()` is now the faithful port and is wired into the x and
w exception paths, so `luxar`, `newton`, `wolfram`, `darwin` and `whisky` all
match. One word still does not:

| Input | pycotovia | Upstream |
|-------|-----------|----------|
| `twist` | `twi^st` | `tewi^st` |

`twist` is an exact match in `w_pronunciase_u`, so the `w` becomes `u` and the
form should be `tui^st`. The binary's extra `e` is not explained yet.

**A one-letter word alone on a line loses the open/closed opposition.** The
binary transcribes `é` as `e^` and `ó` as `o^` when the whole input line is
that single letter, but `E^` and `O^` as soon as any other word is present:

```
[é]     -> e^        [é bo]  -> E^ Bo^
[ó]     -> o^        [ó bo]  -> O^ Bo^
[só]    -> sO^       [nós]   -> nO^s
```

Longer one-word lines are unaffected, so this is specific to single-character
words. pycotovia opens them in every position. The cause is not identified
yet, and the input is degenerate — Cotovia is a sentence-level system — so
this is recorded rather than replicated. It matters only if you call the API
one word at a time with a bare `é` or `ó`. Every parity number in this
document is measured on sentences, so it is not affected.

## Where the remaining gap is

Every differing token at `tra=4` over the 5000-sentence corpus, grouped by
cause:

| Class | Count | Cause |
|-------|-------|-------|
| Letter case on `d`, `b`, `g` | 420 | Pause markers. The binary's `#%pausa%#` puts the next word in phrase-initial position, so the stop stays occlusive. pycotovia has no pause model, so the rule engine makes it fricative. |
| Tonicity (`^`) | 603 | The Viterbi category tagger. `sobre`, `onde`, `segundo`, `contra`, `baixo`, `un`, `e` and `i` change tonicity with their category. |
| Letter case on `e`, `o` | 477 | Vowel timbre, mostly verb forms: `foron`, `temas`, `lemos`, `teñen`. `manexo_do_timbre_verbal()` and `verbos.txt` are not ported. |
| Segmental | see note | The `ao`/`aos` contraction (209 tokens) and the exception-list lookup are now ported. What remains is the syllabification of vowel sequences (`maior`, `muíños`, `incluíndo`, `saíu`). |
| Token count | 448 sentences | Text normalisation: abbreviations (`vol.` → `volume`, `páx.` → `páxina`, `r/` → `rúa`), acronyms spelled letter by letter (`NBA` → `ene be a`), and numerals. |

Pause markers therefore change the phoneme string. They are not cosmetic.

## Reproducing these numbers

Build both oracles as described in [oracles.md](oracles.md), then:

```bash
# The headline numbers: default pycotovia against the fixed build.
python3 tools/parity_harness.py corpus.txt --oracle fixed --json report.json

# keep_bugs=True against stock upstream.
python3 tools/parity_harness.py corpus.txt --oracle pristine

# Both, plus the divergence table between the two builds.
python3 tools/parity_harness.py corpus.txt --oracle both
```

The corpus is plain text, one sentence per line, with no sentence-final
punctuation. The harness adds it. Give the binary one sentence per process:
piping many lines in at once makes it merge some of them.

The in-repo regression suite runs separately. It expects the fixed build at
`../cotovia-mirror/bin/cotovia` and the pristine build at
`../cotovia-pristine/bin/cotovia`, overridable with `COTOVIA_BIN` and
`COTOVIA_BIN_PRISTINE`:

```bash
python3 -m pytest tests/test_parity.py
```

---
[← Limitations](limitations.md) · [Home](../README.md) · [Oracles →](oracles.md)
