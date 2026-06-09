# pycotovia

Pure-Python G2P (grapheme-to-phoneme) phonemizer for **Galician** and **Spanish**, based on the [Cotovia](http://webs.uvigo.es/gtm_voz) TTS system.

## Features

- **Two languages** — Galician (`gl`) and Spanish (`es`) with language-specific exception lists and rewrite rules.
- **Zero dependencies** — pure Python, no C extensions, no heavy ML models.
- **Fast enough** — single-word latency is well under 1 ms on modern hardware.
- **Parity-tested** — verified against the original Cotovia C binary for Galician (see [docs/parity.md](docs/parity.md)).
- **IPA output** — optional mapping from Cotovia phoneme symbols to IPA.

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

## CLI

```bash
# Galician
echo "Ola mundo" | pycotovia

# Spanish
echo "Hola mundo" | pycotovia -l es

# From file
cat words.txt | pycotovia -l gl > phonemes.txt
```

## Differences from the Cotovia binary

| Aspect | pycotovia | Cotovia C binary |
|--------|-----------|------------------|
| Timbre (open/closed e/o) | Not applied in transcription mode | Same — only used for voice-building |
| Stress in `bui`, `fui`, `cuido` | Correctly shifts to `u` (`buj`, `fuj`, `kujDo`) | Bug: keeps stress on `i` (`bwi`, `fwi`, `kwiDo`) due to a precedence error in `aguda()` / `grave()` |

See [docs/parity.md](docs/parity.md) for the full parity test results and the deliberate divergences.

## Documentation

- [docs/architecture.md](docs/architecture.md) — pipeline overview and module map
- [docs/parity.md](docs/parity.md) — verification against the Cotovia binary
- [docs/api.md](docs/api.md) — public API reference

## Examples

See the [examples/](examples/) directory for:
- `basic_usage.py` — single words, phrases, and IPA
- `spanish_usage.py` — Spanish-specific examples
- `phrase_processing.py` — batch processing from a file

## License

Apache-2.0 — this is a clean-room reimplementation in Python, not a derivative of the C++ source.

## Acknowledgements

This is a clean-room port of the Cotovia G2P subsystem (transcription rules, syllabification, stress assignment, and exception lists) from C++ to Python. Cotovia was developed by the Multimedia Technologies Group at the University of Vigo and the Centro Ramón Piñeiro for Research in Humanities.
