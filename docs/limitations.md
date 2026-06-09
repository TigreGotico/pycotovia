# Limitations

This document describes what pycotovia does **not** do, so you can decide if it fits your use case.

## No context awareness

Each word is processed in isolation. The G2P engine has no memory of previous words and no lookahead.

- **"read"** (past) and **"read"** (present) get the same phonemes
- **"live"** (verb) and **"live"** (adjective) get the same phonemes
- **"tear"** (rip) and **"tear"** (from eye) get the same phonemes

If you need context-dependent pronunciation, you need a tagger (POS tagger) or an ML model before the G2P stage.

## No named entity handling

Proper nouns are treated as regular words. This means:

- "Houston" → `ouston` (the `H` is silent, which is correct for Spanish, but not for English)
- "John" → `jon` (Spanish approximation, not English `dʒɒn`)
- "Paris" → `paris` (French `paʁi` is not reproduced)

If you need accurate pronunciation of foreign names, you need a language-specific G2P for that language.

## No dialect support

Only standard Galician and standard Spanish are supported.

- **Spanish**: only Castilian (Spain) pronunciation, not Latin American variants
- **Galician**: only standard Galician, not dialectal variations

For example, Latin American Spanish `s` before consonant is often aspirated (like `h`), but this is not reproduced.

## No number expansion

Digits are treated as non-letters and ignored:

- "123" → `` (empty)
- "1st" → `st` (the `1` is stripped)

If you need to pronounce numbers, you need a text normalization step before pycotovia.

## No abbreviations

Abbreviations are treated as regular words:

- "Dr." → `dr` (the `.` is stripped)
- "Mr." → `mr` (the `.` is stripped)
- "S.A." → `sa` (the `.` is stripped, and the result is wrong)

If you need to expand abbreviations, you need a text normalization step.

## No punctuation handling

Punctuation is stripped during tokenization:

- "Hello, world!" → `hello world` (the `,` and `!` are removed)
- "¿Cómo?" → `como` (the `¿` and `?` are removed)

This is intentional for G2P — the punctuation does not affect pronunciation. But if you need to preserve punctuation for downstream tasks (e.g., prosody modeling), you need to handle it separately.

## No prosody

pycotovia only produces phonemes. It does not produce:

- **Intonation** — pitch contours for questions, statements, exclamations
- **Rhythm** — stress timing, syllable duration
- **Pauses** — phrase boundaries, breathing points

If you need prosody, you need a separate prosody model (e.g., the Cotovia prosody module, or an ML model).

## No ML or neural networks

pycotovia is a rule-based system. It does not use:

- Neural networks
- Deep learning
- Machine learning
- Statistical models

The rules are hand-crafted (originally by the Cotovia authors) and cover the regular phonology of the language. This means:

- **Predictable** — the same input always produces the same output
- **Fast** — no GPU required, no model loading
- **Limited** — cannot learn from data, cannot adapt to new words

## No language detection

You must specify the language (`lang="gl"` or `lang="es"`). There is no automatic language detection.

If you process a Galician text with `lang="es"`, the `x` will be pronounced as /ks/ instead of /ʃ/, and vice versa.

## No tone or length distinctions

Galician and Spanish do not use tone or vowel length to distinguish meaning (unlike Mandarin or Japanese), so this is not a limitation of the language. But if you need tone or length markers for some other purpose, pycotovia does not produce them.

## When to use pycotovia

pycotovia is ideal for:

- **TTS frontends** — generating phoneme strings for speech synthesis
- **Pronunciation dictionaries** — batch-processing word lists
- **Language learning tools** — showing pronunciation of words
- **Phonetic analysis** — studying Galician/Spanish phonology

pycotovia is NOT ideal for:

- **Named entity recognition** — it does not know what is a name
- **Speech recognition** — it goes text→phonemes, not phonemes→text
- **Cross-lingual pronunciation** — it only does Galician/Spanish
- **Real-time prosody** — it does not produce intonation or timing

## Workarounds

For many limitations, the workaround is to add a preprocessing step:

```
Raw text → Normalizer → pycotovia → Post-processor → Output
```

The normalizer can handle:
- Number expansion
- Abbreviation expansion
- Language detection
- Named entity marking

The post-processor can add:
- Prosody markers
- Punctuation restoration
- Timing information

## See also

- `docs/phonetics.md` — phonetics background
- `docs/algorithm.md` — full algorithm walkthrough
- `docs/phonemes.md` — phoneme inventory
- `docs/exceptions.md` — exception word lists
