"""Exception word lists — ported from trat_fon.cpp."""

from .lookup import buscar_inicio


class AlphabetError(ValueError):
    """Raised when an unsupported output alphabet is requested."""


class UnmappedSymbolError(ValueError):
    """Raised when a native Cotovía phoneme has no mapping to the requested
    output alphabet in scriptconv's conversion tables."""



X_PASA_A_KS = [
    "amplex", "anafilax", "anaptix", "anex", "anorex", "anor\xe9x",
    "antitoxi", "apirex", "apodix", "aprox", "asex", "asfix",
    "atarax", "atax", "autotax", "auxi", "auxo", "axes", "axia",
    "axila", "axio", "axoi", "axom", "baux", "biconvex", "bisex",
    "boxe", "caquex", "carbox", "catalex", "coax", "coex",
    "complexi\xf3", "conex", "convex", "coxal", "crucifixi",
    "desconex", "desintoxi", "desoxi", "dexio", "dislex", "dox",
    "eflux", "epistax", "ex",
    "filoxer", "flex", "fluxi", "fluxom",
    "galaxi", "heterodox", "heterosex", "hexa", "hexo",
    "hidroxi", "homosex", "index", "inflex", "intermax",
    "intox", "irreflex", "ixi", "ixo",
    "laxan", "laxat", "laxi", "laxa", "laxo", "lexem", "l\xe9xic",
    "luxa", "marxis", "maxil", "m\xe1xim", "mitilotox", "mix",
    "monoxi", "morfoxintax", "nex",
    "ortodox", "ox",
    "paralax", "paratax", "parox", "pirex", "profilax",
    "proxene", "proxi", "pr\xf3xi",
    "radiotax", "reex", "reflexi", "retroflex",
    "sax", "sexis", "sexo", "sext", "sexua", "sexy", "sintax",
    "six", "submax", "taxat", "taxi", "taxo", "tirox",
    "toxem", "toxi", "toxop", "unisex", "ux", "vexil", "\xe9xito",
]

PRONUNCIANSE_CON_XE = [
    "complexo", "exacu", "execu", "exem", "exerc",
    "exerd", "exip", "ex\xe9rc", "oxal\xe1", "oxiv",
    "saxit", "saxon", "ux\xed",
    "xerogl", "xeron", "xeros",
]

W_PRONUNCIASE_GU = [
    "darwi", "hawa", "sandwi", "taiwa",
    "walk", "wash", "whisk", "winch", "wind",
]

W_PRONUNCIASE_U = [
    "twist", "newto",
]


def _prefix_match(word: str, wordlist: list[str]) -> bool:
    """Prefix lookup, exactly as the binary does it.

    The C calls ``comprobar_en_lista_de_inicio_de_palabras()``, a binary
    search followed by a backward scan. Several of these lists are not fully
    sorted, so some entries are unreachable and the binary never matches
    them. A linear scan would match them and would transcribe real words
    differently from the binary. See docs/parity.md.
    """
    return buscar_inicio(tuple(wordlist), word.lower()) >= 0


def trata_excepcions_xe(word: str, target: str, lang: str = "gl") -> str | None:
    """Rewrite ``x`` as ``ks`` in ``target`` where the word calls for it.

    Port of ``tratamento_das_excepcions_da_xe()``.  ``word`` is the plain
    orthographic word, used only for the list lookups; ``target`` is the
    syllabified and stressed form that gets rewritten.  Keeping the two apart
    matters: a final ``-x`` is a consonant ending and decides where the stress
    lands, so the substitution has to happen *after* stress assignment.

    Returns the rewritten string, or None when nothing applies.
    """
    target_lower = target.lower()
    idx = target_lower.find('x')
    if idx < 0:
        return None

    # Every word that ends in -x sounds as ks.  The C checks this before it
    # consults either list and returns immediately, so it wins over the
    # pronuncianse_con_xe exceptions.
    if target_lower.endswith('x'):
        return target[:-1] + "ks"

    if _prefix_match(word, PRONUNCIANSE_CON_XE):
        return None
    if lang == "gl" and not _prefix_match(word, X_PASA_A_KS):
        return None

    # A syllable boundary in front of the x splits the resulting cluster.
    if idx > 0 and target[idx - 1] == '-':
        return target[:idx - 1] + "k-s" + target[idx + 1:]
    return target[:idx] + "ks" + target[idx + 1:]


def trata_excepcions_w(word: str, target: str) -> str | None:
    """Rewrite ``w`` in ``target`` — port of ``tratamento_das_excepcions_da_w()``.

    ``word`` drives the list lookups, ``target`` is the syllabified and
    stressed form that gets rewritten.
    """
    if 'w' not in target.lower():
        return None

    # The C loops until no `w` is left, and falls back to `b` for every word
    # that is in neither list. Rewriting only the first `w`, or leaving the
    # fallback to the rule engine, gives different output for `newton` and
    # `wolfram`.
    as_u = _prefix_match(word, W_PRONUNCIASE_U)
    as_gu = _prefix_match(word, W_PRONUNCIASE_GU)
    result = target
    while True:
        idx = result.find('w')
        if idx < 0:
            idx = result.find('W')
        if idx < 0:
            break
        if as_u:
            replacement = "u"
        elif as_gu:
            replacement = "gu"
        else:
            replacement = "b"
        result = result[:idx] + replacement + result[idx + 1:]
    return result
