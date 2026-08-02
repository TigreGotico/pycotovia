# pycotovia

[![license: GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](LICENSE)
[![vibe coded](https://img.shields.io/badge/vibe--coded-%F0%9F%A4%96-ff69b4.svg)](#how-this-port-was-made-and-its-licence-please-read)

Pure-Python G2P (grapheme-to-phoneme) phonemizer for **Galician** and **Spanish**, based on the [Cotovia](http://webs.uvigo.es/gtm_voz) TTS system.

## Features

- **Two languages**: Galician (`gl`) and Spanish (`es`) with language-specific exception lists and rewrite rules.
- **One tiny dependency**: pure Python, no C extensions, no heavy ML models — [scriptconv](https://github.com/TigreGotico/scriptconv) is the only requirement.
- **Fast enough**: single-word latency is well under 1 ms on modern hardware.
- **Parity-tested**: verified against the original Cotovia C binary for Galician (see [docs/parity.md](docs/parity.md)).
- **Multi-alphabet output**: native Cotovía notation, IPA, X-SAMPA, ARPABET, Lexique, Kirshenbaum, or RFE, picked with one argument.

## Installation

```bash
pip install pycotovia
```

Requires Python >= 3.11.

## Quick start

```python
import pycotovia

# Galician (default)
print(pycotovia.phonemize("Ola, como estás?"))      # → "ola komo estajs"
print(pycotovia.phonemize("guerra", lang="gl"))      # → "gerra"

# Spanish
print(pycotovia.phonemize("México", lang="es"))      # → "meksiko"
print(pycotovia.phonemize("México", lang="gl"))      # → "meSiko"

# IPA mapping
print(pycotovia.cotovia_to_ipa("gerra"))              # → "ɣɛra"
```

## Output alphabets

pycotovia's native output is Cotovía notation — the phoneme symbols of the
original Cotovía TTS engine. The `alphabet` argument converts that native
output to any alphabet supported by [scriptconv](https://github.com/TigreGotico/scriptconv):

```python
import pycotovia

print(pycotovia.ALPHABETS)
# ('cotovia', 'ipa', 'arpa', 'x-sampa', 'lexique', 'kirshenbaum', 'rfe')

print(pycotovia.phonemize("guerra", lang="gl"))                        # → "gerra "  (native, default)
print(pycotovia.phonemize("guerra", lang="gl", alphabet="ipa"))        # → "ɡera "
print(pycotovia.phonemize("cantar", lang="gl", alphabet="x-sampa"))    # → "kanta4 "
```

The default stays the native Cotovía notation, so existing calls are unaffected.
Conversion only applies at `tra=1` (phonemes only) — the stress and syllable
markers available at higher `tra` levels have no equivalent in the other
notations.

A symbol with no equivalent in the target alphabet raises `UnmappedSymbolError`
rather than being dropped or mistranslated. An unknown alphabet name raises
`AlphabetError`, listing the accepted values.

## CLI

```bash
# Galician
echo "Ola mundo" | pycotovia

# Spanish
echo "Hola mundo" | pycotovia -l es

# IPA output
echo "Ola mundo" | pycotovia -a ipa

# From file
cat words.txt | pycotovia -l gl > phonemes.txt
```

## Differences from the Cotovia binary

| Aspect | pycotovia | Cotovia C binary |
|--------|-----------|------------------|
| Timbre (open/closed e/o) | Not applied in transcription mode | Same: only used for voice-building |
| Stress in `bui`, `fui`, `cuido` | Correctly shifts to `u` (`buj`, `fuj`, `kujDo`) | Bug: keeps stress on `i` (`bwi`, `fwi`, `kwiDo`) due to a precedence error in `aguda()` / `grave()` |

See [docs/parity.md](docs/parity.md) for the full parity test results and the deliberate divergences.

## Documentation

- [docs/architecture.md](docs/architecture.md): pipeline overview and module map
- [docs/parity.md](docs/parity.md): verification against the Cotovia binary
- [docs/api.md](docs/api.md): public API reference

## Examples

See the [examples/](examples/) directory for:
- `basic_usage.py`: single words, phrases, IPA output
- `spanish_usage.py`: Spanish-specific examples
- `phrase_processing.py`: batch processing from a file

## How this port was made, and its licence (please read)

This is an **AI-assisted, human-guided, test-driven** port. An AI assistant read
the public Cotovia C++ source and reimplemented the G2P subsystem (transcription
rules, syllabification, stress assignment, exception lists) in Python. A human
guided the effort and validated results against the original Cotovia binary. The
human collaborators **never read the Cotovia C++ source themselves**: they drove
and checked the work through the binary.

Because the implementing AI **read the GPL source**, this is **not a clean-room
reimplementation** and we make no such claim. It is a source-derived port.
Cotovia is **GPL-licensed**, so to honour the original work this project is
licensed **GPL-3.0-or-later** (see [LICENSE](LICENSE)).

**Open questions we want to be transparent about** (not legal advice):

- *Was this clean-room?* No: the implementing agent read the GPL source.
- *Could it be relicensed permissively?* Almost certainly not. A port derived
  from GPL source is a derivative work, so we keep GPL.
- *Can an AI originate or "assign" a licence?* Unsettled: authorship/copyright of
  AI-generated code is legally unclear. We apply GPL-3.0 as the conservative,
  upstream-respecting default rather than asserting any novel rights.

## Acknowledgements

The Cotovia G2P rules, syllabification, stress assignment and exception lists
this port derives from are the work of the **Multimedia Technologies Group,
University of Vigo** and the **Centro Ramón Piñeiro para a Investigación en
Humanidades**. This credit does not imply their endorsement.
