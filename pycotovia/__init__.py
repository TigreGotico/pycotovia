"""pycotovia — pure-Python Cotovia G2P phonemizer for Galician and Spanish."""

from .phonemize import phonemize, Phonemizer
from .phonemes import COTOVIA2IPA, cotovia_to_ipa
from .alphabets import ALPHABETS, NATIVE_ALPHABET
from .exceptions import AlphabetError, UnmappedSymbolError

__version__ = "0.1.0"
