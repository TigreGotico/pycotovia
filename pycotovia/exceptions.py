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
    "proxene", "proxi", "pr\xf3simo",
    "radiotax", "reex", "reflexi", "retroflex",
    "sax", "sexis", "sexo", "sext", "sexua", "sexy", "sintax",
    "six", "submax", "taxat", "taxi", "taxo", "tirox",
    "toxem", "toxi", "toxop", "unisex", "ux", "vexil", "\xe9xito",
]

PRONUNCIANSE_CON_XE = [
    "complexo", "exacu", "execu", "exem", "exerc",
    "exerd", "exip", "ex\xe9rc", "oxal\xe1", "oxiv",
    "saxit", "saxon", "ux\xe1",
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


def trata_excepcions_xe(word: str, lang: str = "gl") -> str | None:
    word_lower = word.lower()

    if lang == "gl":
        if _prefix_match(word, PRONUNCIANSE_CON_XE):
            return None
        if _prefix_match(word, X_PASA_A_KS):
            idx = word_lower.index('x')
            return word[:idx] + "ks" + word[idx + 1:]
        return None
    else:
        if _prefix_match(word, PRONUNCIANSE_CON_XE):
            return None
        if 'x' in word_lower:
            idx = word_lower.index('x')
            return word[:idx] + "ks" + word[idx + 1:]
        return None


def trata_excepcions_w(word: str) -> str | None:
    if _prefix_match(word, W_PRONUNCIASE_U):
        idx = word.lower().index('w')
        return word[:idx] + "u" + word[idx + 1:]
    if _prefix_match(word, W_PRONUNCIASE_GU):
        idx = word.lower().index('w')
        return word[:idx] + "gu" + word[idx + 1:]
    return None
