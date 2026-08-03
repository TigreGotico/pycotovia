"""Pipeline orchestrator — input text → phoneme string.

Matches the Cotovia binary pipeline exactly:
  1. Input text is normalized and split into words
  2. Each word: exception preprocessing → syllabification → stress → timbre
  3. Words are joined into a single phrase: "## word1 word2 ##"
  4. All G2P rewrite rules are applied to the full phrase
  5. Final output strips pause markers, stress marks, and syllable separators
     matching the binary's -t0 mode (phonemes only)
"""

from .charset import letra, to_minusculas
from .exceptions import trata_excepcions_xe, trata_excepcions_w, AlphabetError
from .syllabify import syllabify
from .stress import assign_stress
from .timbre import assign_timbre
from .engine import apply_rules
from .rules_data import GALEGO_RULES_SV, CASTELLANO_RULES_SV
from .alphabets import ALPHABETS, NATIVE_ALPHABET, to_alphabet

#: Word-internal hyphen, kept by the tokenizer so :func:`_split_hyphenated`
#: can decide whether it joins or separates two words.
HYPHEN = '-'

#: Allomorphs of the article that Cotovia attaches to the preceding verb form
#: when they follow a hyphen: ``amosa-lo`` is the single word ``amosalo``.
#: Any other suffix (``-lle``, ``-me``, ``-nos``, ``-estar``) is a word of its
#: own.  Verified against the binary at ``-St1lgl``.
ARTICLE_ALLOMORPHS = frozenset({"lo", "la", "los", "las"})


def _split_hyphenated(token: str) -> list[str]:
    """Resolve a hyphen-bearing token into one or more words.

    Runs of hyphens act as a single separator, and leading/trailing hyphens
    are dropped, matching the binary (``amosa--lo`` → ``amosalo``,
    ``-lo`` → ``lo``, ``amosa-`` → ``amosa``).
    """
    parts = [p for p in token.split(HYPHEN) if p]
    if not parts:
        return []
    if len(parts) == 2 and parts[1].lower() in ARTICLE_ALLOMORPHS:
        return ["".join(parts)]
    return parts


#: Marks that end a sentence for the binary, which then transcribes what
#: follows as a new phrase.  Verified against the binary, which prints one
#: line per sentence: "veu: voulles" splits, "veu? voulles" and
#: "veu, voulles" do not.  Getting this wrong leaves the first word of the
#: next sentence in intervocalic position, so /b/ comes out fricative (B)
#: where the binary has the phrase-initial occlusive (b).
SENTENCE_SEPARATORS = ".:;"


def _split_sentences(text: str) -> list[str]:
    """Split input text into the sentences the binary would transcribe."""
    parts = []
    current = []
    for ch in text:
        if ch in SENTENCE_SEPARATORS:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    parts.append("".join(current))
    return [p for p in parts if p.strip()]


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

    def phonemize(self, text: str, tra: int = 1, alphabet: str = NATIVE_ALPHABET) -> str:
        """Convert plain text to a phoneme string.

        Args:
            text: Input text (Latin-1 or Unicode)
            tra: Output level (1=phonemes, 2=+stress, 3=+syllables, 4=raw)
            alphabet: Output phonetic alphabet. Defaults to pycotovia's
                native Cotovía notation (no behavior change from prior
                releases). Any other value is produced by converting the
                native output through scriptconv; see :data:`ALPHABETS` for
                the full list of accepted identifiers. Only valid together
                with ``tra=1`` — alphabet conversion is not defined over the
                stress/syllable-separator markers emitted at higher levels.

        Returns:
            Phoneme string in the requested alphabet.
        """
        # Step 1: Split into sentences.  Each one is wrapped in its own pair
        # of silence markers, which is what puts its first word in
        # phrase-initial position for the sandhi rules.
        parts = []
        for sentence in _split_sentences(text):
            words = self._tokenize(sentence)
            if not words:
                continue

            # Step 2: Process each word through the pre-rules pipeline
            processed_words = [self._preprocess_word(w) for w in words]

            # Step 3: Join into a phrase with silence wrappers (matching binary)
            phrase = "## " + " ".join(processed_words) + " ##"

            # Step 4: Apply the G2P rewrite rules to the whole phrase
            phoneme_phrase = apply_rules(phrase, self.rules)

            # Step 5: Strip per tra level
            if tra >= 4:
                parts.append(phoneme_phrase)
            else:
                parts.append(_strip_t0(phoneme_phrase, tra=tra))
        result = "".join(parts)

        # Step 6: Convert to the requested output alphabet, if not native
        if alphabet != NATIVE_ALPHABET:
            if tra != 1:
                raise AlphabetError(
                    "alphabet conversion is only supported with tra=1 "
                    "(phonemes only) — stress/syllable markers have no "
                    "equivalent in other notations"
                )
            result = to_alphabet(result, alphabet)

        return result

    def _tokenize(self, text: str) -> list[str]:
        """Split text into words.

        A hyphen inside a word is not a word boundary on its own.  Cotovia
        joins ``verbo-lo`` into a single word when the part after the hyphen
        is one of the article allomorphs ``lo/la/los/las`` (``amosa-lo`` →
        ``amosalo``), and splits it into two words otherwise (``ben-estar`` →
        ``ben`` + ``estar``).  Getting this wrong shifts every later word of
        the sentence out of alignment.
        """
        words: list[str] = []
        current: list[str] = []
        for ch in text.strip():
            if letra(ch) or ch == HYPHEN:
                current.append(ch)
            else:
                if current:
                    words.extend(_split_hyphenated("".join(current)))
                    current = []
        if current:
            words.extend(_split_hyphenated("".join(current)))
        return words

    def _preprocess_word(self, word: str) -> str:
        """Apply pre-rule processing to a single word.

        Pipeline: lowercase → syllabify → stress → x/w exceptions.

        The exceptions run last, on the syllabified and stressed form, because
        that is the order ``Trat_fon::trat_fonetico()`` uses: it passes the
        plain word for the list lookups and mutates ``pal_sil_e_acentuada``.
        Running them earlier changes where the stress lands for words that end
        in ``-x`` (``index`` → ``inde^ks``, not ``i^ndeks``).
        """
        # Lowercase — matches pasar_a_minusculas() in the C binary
        w = to_minusculas(word)

        s = syllabify(w)
        s = assign_stress(s, self.lang)

        xe_result = trata_excepcions_xe(w, s, self.lang)
        if xe_result is not None:
            s = xe_result
        w_result = trata_excepcions_w(w, s)
        if w_result is not None:
            s = w_result

        # NOTE: vowel timbre (assign_timbre) is deliberately NOT applied here.
        # It belongs to atono_ou_tonico_aberto_ou_pechado_e_w_x(), which the
        # binary calls from its main pipeline (cotovia.cpp:2911) and which
        # shows up only in `-t3` output.  pycotovia has no -t3-equivalent mode
        # yet, so the stage is unported and timbre.py is currently unused.
        # (An older comment here claimed the C call was commented out, citing
        # transcripcion.cpp:741 — that copy is dead, but the cotovia.cpp one
        # is live.  See docs/parity.md.)

        return s


def phonemize(text: str, lang: str = "gl", tra: int = 1, alphabet: str = NATIVE_ALPHABET) -> str:
    """Convenience function — phonemize text in one call."""
    p = Phonemizer(lang)
    return p.phonemize(text, tra=tra, alphabet=alphabet)
