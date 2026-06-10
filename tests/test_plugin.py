"""Tests for pycotovia.plugin — CotoviaSyllabifier and PycotoviaG2PPlugin."""
import pytest

from pycotovia.plugin import CotoviaSyllabifier, PycotoviaG2PPlugin
from orthography2ipa.g2p_plugin import G2PPlugin
from orthography2ipa.syllabifier_plugin import SyllabifierPlugin


# ---------------------------------------------------------------------------
# CotoviaSyllabifier — round-trip and language coverage
# ---------------------------------------------------------------------------

SYLLABIFY_CASES = [
    # word           expected syllables
    ("casa",         ["ca", "sa"]),
    ("cantar",       ["can", "tar"]),
    ("ciencia",      ["cien", "cia"]),          # diphthong
    ("traer",        ["tra", "er"]),            # hiatus
    ("muiño",        ["mui", "ño"]),            # diphthong ui
    ("auga",         ["au", "ga"]),             # diphthong au
    ("corazón",      ["co", "ra", "zón"]),      # trisyllabic + accent
    ("tranvía",      ["tran", "ví", "a"]),      # hiatus after accent
]


@pytest.fixture(scope="module")
def syllabifier():
    return CotoviaSyllabifier()


def test_syllabifier_isinstance(syllabifier):
    assert isinstance(syllabifier, SyllabifierPlugin)


def test_syllabifier_language_codes(syllabifier):
    codes = syllabifier.language_codes
    assert "gl" in codes
    assert "gl-ES" in codes
    assert "es-ES" in codes


@pytest.mark.parametrize("word,expected", SYLLABIFY_CASES)
def test_syllabifier_output(syllabifier, word, expected):
    result = syllabifier.syllabify(word)
    assert result == expected, f"syllabify({word!r}) = {result!r}, expected {expected!r}"


@pytest.mark.parametrize("word,_", SYLLABIFY_CASES)
def test_syllabifier_roundtrip(syllabifier, word, _):
    """Joining syllables must exactly rebuild the original word."""
    syllables = syllabifier.syllabify(word)
    assert "".join(syllables) == word, (
        f"round-trip failed for {word!r}: {''.join(syllables)!r}"
    )


# ---------------------------------------------------------------------------
# Entry-point discovery
# ---------------------------------------------------------------------------

def test_entry_point_discovery():
    """orthography2ipa.get_syllabifier('gl') must return CotoviaSyllabifier."""
    import orthography2ipa.registry as reg

    # Force re-discovery so the test is not sensitive to import order
    reg._syllabifiers = None
    plugin = reg.get_syllabifier("gl")
    assert plugin is not None, "No syllabifier registered for 'gl'"
    assert isinstance(plugin, CotoviaSyllabifier)


# ---------------------------------------------------------------------------
# PycotoviaG2PPlugin — conformance and IPA output
# ---------------------------------------------------------------------------

COTOVIA_INTERNAL = {
    "B", "D", "G", "J", "N", "O", "E", "S", "T", "Z",
    "tS", "rr", "L", "jj",
}


@pytest.fixture(scope="module")
def g2p():
    return PycotoviaG2PPlugin()


def test_g2p_isinstance(g2p):
    assert isinstance(g2p, G2PPlugin)


def test_g2p_language_codes(g2p):
    assert "gl" in g2p.language_codes


def test_g2p_transcribe_returns_string(g2p):
    result = g2p.transcribe("casa")
    assert isinstance(result, str)
    assert result  # non-empty


def test_g2p_no_cotovia_symbols_leak(g2p):
    """transcribe() output must not contain raw Cotovia internal symbols."""
    text = "ciencia muiño traer auga"
    result = g2p.transcribe(text)
    for sym in COTOVIA_INTERNAL:
        assert sym not in result, (
            f"Cotovia symbol {sym!r} leaked into IPA output: {result!r}"
        )


def test_g2p_transcribe_word(g2p):
    result = g2p.transcribe_word("galego")
    assert isinstance(result, str)
    assert result


def test_g2p_parity_with_pipeline():
    """Plugin.transcribe must equal the raw pipeline output mapped to IPA."""
    from pycotovia.phonemize import Phonemizer
    from pycotovia.phonemes import cotovia_to_ipa

    text = "lingua galega"
    raw = Phonemizer("gl").phonemize(text, tra=1)
    expected_ipa = cotovia_to_ipa(raw).strip()

    plugin = PycotoviaG2PPlugin()
    assert plugin.transcribe(text) == expected_ipa
