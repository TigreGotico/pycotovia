# TODO

## Backlog

- [ ] Add more test cases (edge cases, loanwords, proper nouns)
- [ ] Add CI via GitHub Actions (pytest, parity test)
- [ ] Add `__main__.py` support for `python -m pycotovia` (done)
- [ ] Publish to PyPI
- [ ] Add `docs/phonemes.md` with full phoneme inventory
- [ ] Add `docs/exceptions.md` documenting exception lists
- [ ] Add `docs/contributing.md`
- [ ] Add benchmark script comparing py vs C binary speed
- [ ] Add `lang="auto"` detection (naive: Galician if word in Galician exception list)
- [ ] Add support for `tra=5` (phoneme + syllable + stress + raw)
- [ ] Add `pycotovia.segment(word)` API returning structured syllables
- [ ] Add IPA output with stress markers
- [ ] Add `pycotovia.phonemize_file()` convenience for batch processing
- [ ] Add more comprehensive Spanish parity test
- [ ] Add type stubs for public API
- [ ] Add `docs/changelog.md`

## Done

- [x] Fix triphthong bug (`uia` → `guia`)
- [x] Document deliberate divergence from C binary (bui/fui/cuido)
- [x] Add README.md
- [x] Add docs/ and examples/
- [x] Add tests/ with parity test
- [x] Add __main__.py
- [x] Add LICENSE
- [x] Add AGENTS.md and TODO.md
- [x] Fix pyproject.toml metadata
