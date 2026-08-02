"""Output-alphabet conversion — bridges pycotovia's native Cotovía notation
to any phonetic alphabet supported by scriptconv (IPA, X-SAMPA, ARPABET,
Lexique, Kirshenbaum, RFE, ...).

pycotovia always produces its native Cotovía-notation phoneme string first.
Any other requested alphabet is reached by converting that native string
through scriptconv's ``cotovia`` convention, pivoting through IPA.
"""

from scriptconv import Notation, can_convert, convert, UnknownSymbolError

from .exceptions import AlphabetError, UnmappedSymbolError

NATIVE_ALPHABET = "cotovia"

#: Alphabets pycotovia can emit, keyed by the string identifier accepted by
#: the ``alphabet=`` argument of :func:`pycotovia.phonemize`. Enumerated from
#: scriptconv's own convention registry rather than hardcoded, so new
#: notations scriptconv adds are picked up automatically.
ALPHABETS: tuple[str, ...] = (NATIVE_ALPHABET,) + tuple(
    n.value for n in Notation if can_convert(NATIVE_ALPHABET, n.value)
)


def to_alphabet(native: str, alphabet: str) -> str:
    """Convert a native Cotovía phoneme string to *alphabet*.

    Args:
        native: Phoneme string in pycotovia's native Cotovía notation.
        alphabet: Target alphabet identifier (see :data:`ALPHABETS`).

    Returns:
        The phoneme string rewritten in the target alphabet. Returned
        unchanged when *alphabet* is the native notation.

    Raises:
        AlphabetError: *alphabet* is not one of :data:`ALPHABETS`.
        UnmappedSymbolError: a symbol in *native* has no equivalent in
            scriptconv's Cotovía convention table.
    """
    if alphabet == NATIVE_ALPHABET:
        return native
    if alphabet not in ALPHABETS:
        raise AlphabetError(
            f"Unsupported alphabet {alphabet!r}. "
            f"Choose one of: {', '.join(ALPHABETS)}"
        )
    # Convert word-by-word: pycotovia joins phoneme tokens with plain spaces,
    # which are not themselves part of the Cotovía phoneme inventory, so the
    # whitespace is kept out of scriptconv's strict-mode symbol check and
    # reinserted verbatim afterwards.
    words = native.split(" ")
    try:
        converted = [
            convert(w, NATIVE_ALPHABET, alphabet, errors="strict") if w else w
            for w in words
        ]
    except UnknownSymbolError as e:
        raise UnmappedSymbolError(
            f"Cotovía symbol has no {alphabet!r} mapping in scriptconv: {e}"
        ) from e
    return " ".join(converted)
