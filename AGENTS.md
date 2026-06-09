# pycotovia

## Onboarding

- `pycotovia` is a pure-Python G2P phonemizer for Galician and Spanish.
- It is a port of the Cotovia TTS subsystem.
- Both languages are supported: `lang="gl"` (default) and `lang="es"`.

## Build

```bash
cd /home/miro/AgentWorkspaces/ml/tts/pycotovia
pip install -e .
```

## Test

```bash
cd /home/miro/AgentWorkspaces/ml/tts/pycotovia
python3 -m pytest tests/
```

## Rule regeneration

If the Cotovia source changes:

```bash
python3 extract_rules.py /path/to/cotovia/src/cotovia/include/alof_gal.hpp gl
python3 extract_rules.py /path/to/cotovia/src/cotovia/include/alof_cas.hpp es
```

## Architecture

See `docs/architecture.md`.

## Key differences from the Cotovia binary

- `bui`, `fui`, `cuido` → py places stress on `u` (correct), binary keeps it on `i` due to a C precedence bug.

See `docs/parity.md`.

## Dependencies

None. Pure Python >= 3.11.

## License

GPL-3.0-or-later.
