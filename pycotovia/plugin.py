"""orthography2ipa integration — SyllabifierPlugin + G2PPlugin for Galician.

Two classes are defined here:

- :class:`CotoviaSyllabifier` — component plugin registered in the
  ``orthography2ipa.syllabify`` entry-point group so that orthography2ipa's
  own stress detection syllabifies Galician (and Spanish) with pycotovia's
  port of Cotovia's ``separar_silabas()`` instead of its naive vowel-group
  splitter.

- :class:`PycotoviaG2PPlugin` — full G2P engine for Galician, implementing
  the shared :class:`~orthography2ipa.g2p_plugin.G2PPlugin` interface.
  The Cotovia phonetic alphabet output is mapped to IPA via
  :func:`~pycotovia.phonemes.cotovia_to_ipa` before being returned.

Note: only :class:`CotoviaSyllabifier` is registered as an entry point
(``orthography2ipa.syllabify``).  No ``orthography2ipa.g2p`` entry point is
registered — the G2P plugin is consumed directly by downstream engines
(e.g. phoonnx) rather than through orthography2ipa's own plugin registry.
"""
from typing import List, Optional

from orthography2ipa.g2p_plugin import G2PPlugin, WordContext
from orthography2ipa.syllabifier_plugin import SyllabifierPlugin


class CotoviaSyllabifier(SyllabifierPlugin):
    """Galician/Spanish syllabifier backed by pycotovia's ``separar_silabas()`` port.

    The underlying :func:`pycotovia.syllabify.syllabify` function inserts
    ``-`` markers between syllables.  This wrapper strips those markers from
    the individual syllable strings so that ``'-'.join(result)`` rebuilds
    the word exactly.

    Language coverage:
    - ``gl`` / ``gl-ES`` — Galician (primary target, validated against the
      Cotovia binary).
    - ``es-ES`` — Spanish (the same phonotactic rules apply; the Cotovia
      front-end processes both languages with the same syllabification
      function).
    """

    @property
    def language_codes(self) -> List[str]:
        return ["gl", "gl-ES", "es-ES"]

    def syllabify(self, word: str, lang: Optional[str] = None) -> List[str]:
        """Return a list of syllables whose concatenation rebuilds *word*.

        Args:
            word: Input word (Unicode, orthographic accents allowed).
            lang: BCP-47 language code (ignored — same rules for gl/es).

        Returns:
            List of syllable strings, e.g. ``["ci", "en", "cia"]``.
        """
        from pycotovia.syllabify import syllabify as _syllabify

        syllabified = _syllabify(word)
        return syllabified.split("-")


class PycotoviaG2PPlugin(G2PPlugin):
    """Galician G2P via the pycotovia pipeline, output in IPA.

    The underlying :class:`pycotovia.phonemize.Phonemizer` produces output
    in the Cotovia phonetic alphabet (a GTM/University-of-Vigo internal
    notation); this plugin maps that notation to IPA via
    :func:`pycotovia.phonemes.cotovia_to_ipa` before returning.

    Language codes: ``["gl"]``.  Spanish (``es`` / ``es-ES``) is intentionally
    excluded here — while pycotovia can phonemize Spanish, orthography2ipa
    already has a richer ``es-ES`` spec and separate plugins; exposing ``es``
    from this plugin would create ambiguity.
    """

    def __init__(self, lang: str = "gl") -> None:
        self.lang = lang
        self._phonemizer = None

    @property
    def language_codes(self) -> List[str]:
        return ["gl"]

    def _engine(self):
        if self._phonemizer is None:
            from pycotovia.phonemize import Phonemizer
            self._phonemizer = Phonemizer(lang="gl")
        return self._phonemizer

    def transcribe(self, text: str) -> str:
        """Phonemize *text* and return an IPA string.

        The Cotovia pipeline tokenises, syllabifies, assigns stress and
        applies the full semi-vowel-aware rule table; the resulting Cotovia
        phoneme string is then converted to IPA via
        :data:`pycotovia.phonemes.COTOVIA2IPA`.

        Args:
            text: Input text (plain Galician orthography).

        Returns:
            IPA phoneme string with space-separated word transcriptions.
        """
        from pycotovia.phonemes import cotovia_to_ipa

        cotovia_out = self._engine().phonemize(text, tra=1)
        return cotovia_to_ipa(cotovia_out).strip()

    def transcribe_word(
        self, word: str, context: Optional[WordContext] = None
    ) -> str:
        """Phonemize a single *word* and return its IPA transcription.

        Args:
            word: Single Galician word (no spaces).
            context: Optional :class:`~orthography2ipa.g2p_plugin.WordContext`
                     (unused — pycotovia is context-free at the word level).

        Returns:
            IPA string for the word (trailing whitespace stripped).
        """
        return self.transcribe(word)
