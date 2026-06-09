"""Pipeline orchestrator — input text → phoneme string.

Matches the Cotovia binary pipeline exactly:
  1. Input text is normalized and split into words
  2. Each word: exception preprocessing → syllabification → stress → timbre
  3. Words are joined into a single phrase: "## word1 word2 ##"
  4. All G2P rewrite rules are applied to the full phrase
  5. Final output strips pause markers, stress marks, and syllable separators
     matching the binary's -t0 mode (phonemes only)
"""

from .charset import letra
from .exceptions import trata_excepcions_xe, trata_excepcions_w
from .syllabify import syllabify
from .stress import assign_stress
from .timbre import assign_timbre
from .engine import apply_rules
from .rules_data import GALEGO_RULES_SV, CASTELLANO_RULES_SV


def _strip_t0(s: str, tra: int = 1) -> str:
    """Strip #...# and %...% blocks, ^ and - (matching binary sacar_transcripcion).

    Args:
        s: Raw rule-engine output
        tra: Output level (1=phonemes only, 2=+stress, 3=+sep, 4=raw)
    """
    result = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch == '#':
            i += 1
            while i < n and s[i] != '#':
                i += 1
            i += 1
            # Consume the character after ## (usually a space) —
            # matches C's if(*aux2)aux2++ after the switch
            if i < n:
                i += 1
        elif ch == '%':
            i += 1
            while i < n and s[i] != '%':
                i += 1
            i += 1
            if i < n:
                i += 1
        elif ch == '^':
            if tra > 1:
                result.append(ch)
            i += 1
        elif ch == '-':
            if tra > 2:
                result.append(ch)
            i += 1
        else:
            result.append(ch)
            i += 1
    return "".join(result)


class Phonemizer:
    """G2P phonemizer for Galician and Spanish."""

    def __init__(self, lang: str = "gl"):
        if lang not in ("gl", "es"):
            raise ValueError(f"Unsupported language: {lang!r}. Use 'gl' or 'es'.")
        self.lang = lang
        self.rules = GALEGO_RULES_SV if lang == "gl" else CASTELLANO_RULES_SV

    def phonemize(self, text: str, tra: int = 1) -> str:
        """Convert plain text to a phoneme string.

        Args:
            text: Input text (Latin-1 or Unicode)
            tra: Output level (1=phonemes, 2=+stress, 3=+syllables, 4=raw)

        Returns:
            Phoneme string (Cotovia notation)
        """
        # Step 1: Collect words
        words = self._tokenize(text)

        # Step 2: Process each word through pre-rules pipeline
        processed_words = []
        for word in words:
            processed_words.append(self._preprocess_word(word))

        # Step 3: Join into phrase with silence wrappers (matching binary)
        phrase = "## " + " ".join(processed_words) + " ##"

        # Step 4: Apply G2P rewrite rules to the full phrase
        phoneme_phrase = apply_rules(phrase, self.rules)

        # Step 5: Strip per tra level
        if tra >= 4:
            return phoneme_phrase
        result = _strip_t0(phoneme_phrase, tra=tra)

        return result

    def _tokenize(self, text: str) -> list[str]:
        """Split text into words (whitespace-separated)."""
        words = []
        current = []
        for ch in text.strip():
            if letra(ch):
                current.append(ch)
            else:
                if current:
                    words.append("".join(current))
                    current = []
        if current:
            words.append("".join(current))
        return words

    def _preprocess_word(self, word: str) -> str:
        """Apply pre-rule processing to a single word.

        Pipeline: exceptions → syllabify → stress → timbre
        """
        w = word

        # Exception preprocessing
        xe_result = trata_excepcions_xe(w, self.lang)
        if xe_result is not None:
            w = xe_result
        w_result = trata_excepcions_w(w)
        if w_result is not None:
            w = w_result

        # Syllabify
        s = syllabify(w)

        # Assign stress
        s = assign_stress(s, self.lang)

        # NOTE: Timbre assignment (assign_timbre) is NOT applied here.
        # The binary only uses it for voice-building (-lin mode), not for -t
        # transcription. The pal_sil_e_acentuada fed to transcribe() does NOT
        # carry open/closed e/o marks. See transcribe() line 741:
        #   //atono_ou_tonico_aberto_ou_pechado_e_w_x(frase_sil_e_acentuada,item);
        # That call is COMMENTED OUT in the transcribe path.

        return s


def phonemize(text: str, lang: str = "gl", tra: int = 1) -> str:
    """Convenience function — phonemize text in one call."""
    p = Phonemizer(lang)
    return p.phonemize(text, tra=tra)
