"""Exception word lists — ported from trat_fon.cpp."""


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
    wl = word.lower()
    for entry in wordlist:
        if wl.startswith(entry):
            return True
    return False


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
    idx = target.lower().find('w')
    if idx < 0:
        return None
    if _prefix_match(word, W_PRONUNCIASE_U):
        return target[:idx] + "u" + target[idx + 1:]
    if _prefix_match(word, W_PRONUNCIASE_GU):
        return target[:idx] + "gu" + target[idx + 1:]
    return None
