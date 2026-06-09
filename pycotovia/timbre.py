"""Vowel timbre (open/closed e/o) — port of trat_fon.cpp asignar_timbre_a_sustantivos()."""

from .charset import e_acentuada, o_acentuada, base_vowel

# esdrúxulas (proparoxytones) — closed exceptions
ESDR_TERMINACIONS_PECHADAS = [
    "úa", "uá", "adebé", "adevé", "arepsé", "ocirtné", "olaté", "oramé", "ovacné",
]

ESDR_PALABRAS_PECHADAS = [
    "alvéolo", "améndoa", "auténtico", "bábedo", "bávera", "báchega", "cáreo",
    "cábado", "cánchega", "débede", "et cétera", "lávedo", "lástrego", "máxade",
    "océano", "paréntese", "pártega", "sásega", "trémaro", "témporas", "tépeda",
    "tédalas", "tédolos", "váneto", "xámara",
]

# graves (paroxytones) — closed exceptions
GRAVES_TERMINACIONS_PECHADAS = [
    "abe", "acob", "acrec", "acse", "acso", "ade", "ado", "adro", "ae", "ahce",
    "ahcoc", "ahcre", "alle", "allo", "amo", "arep", "arie", "ario", "aro", "arro",
    "arte", "arto", "ase", "aso", "ate", "atse", "axe", "axo", "aze", "azo", "azro",
    "ede", "emon", "erbo", "ete", "etneulf", "obe", "obo", "ocse", "ocso", "ode",
    "odo", "odro", "oe", "ohce", "oio", "oixe", "olle", "ollo", "olobec", "omert",
    "omo", "onro", "opo", "orde", "orie", "orio", "oro", "orro", "oso", "osro",
    "ote", "oto", "otrop", "otsec", "ove", "ovoc", "oxe", "oxo", "ozere", "ozev",
    "ozo", "ozro", "sece", "sere", "sero", "sese",
]

GRAVES_PALABRAS_PECHADAS = [
    "aborto", "absorto", "aceso", "achega", "achego", "adega", "agosto", "ampola",
    "arrolo", "atropelo", "bancarrota", "becerra", "becerro", "boa", "bocha",
    "bodega", "bodego", "boga", "bola", "bolo", "botaporela", "cabelo", "cachelo",
    "carambelo", "caramelo", "cebola", "cebolo", "cebra", "centola", "centolo",
    "cepa", "cera", "cerro", "chepa", "coco", "cogomelo", "colega", "corpo",
    "cotelo", "crisantemo", "desenrolo", "deuses", "dobra", "doce", "engorde",
    "escoba", "espeso", "este", "estes", "estrela", "estrema", "expreso", "febra",
    "felo", "femia", "galego", "gota", "grego", "grelo", "grolo", "hoxe", "ileso",
    "impreso", "lagosta", "magosto", "manchego", "mangosta", "marmelo", "media",
    "medio", "mesto", "metro", "moca", "moco", "moega", "morbo", "mosto", "moxega",
    "negro", "noca", "noelo", "obseso", "oda", "ola", "omega", "peche", "pega",
    "pelo", "peso", "pexego", "pola", "polo", "preso", "rebolo", "rede", "rego",
    "remo", "repolo", "rolo", "rostro", "rota", "sartego", "seca", "soba", "sopa",
    "sorna", "supremo", "tempero", "teso", "testo", "toco", "tola", "tolo",
    "torre", "trece", "verde", "voo", "xeso", "xofre",
]

GRAVES_PALABRAS_ABERTAS = [
    "adrede", "alboio", "amora", "amorodo", "anexo", "antonte", "arestora",
    "beladona", "borda", "brosa", "cadora", "calabozo", "ceo", "choio", "cobre",
    "coio", "completo", "connosco", "convexo", "convosco", "corda", "corno",
    "credo", "creto", "croio", "defensa", "demora", "demónho", "diabete",
    "diarrea", "dieta", "dona", "dueto", "festa", "flexo", "foresta", "fosa",
    "frecha", "fresa", "glosa", "grosa", "groso", "heterodoxo", "hiena", "idea",
    "indefensa", "isoglosa", "madona", "marea", "meteoro", "moda", "modo", "mora",
    "nantronte", "nexo", "noitevella", "nora", "nosa", "noso", "noutronte",
    "noutrora", "ofensa", "ollo", "onte", "ortodoxo", "outrora", "paradoxo",
    "pesca", "pobre", "pomba", "ponla", "porra", "prensa", "preto", "prosa",
    "protesta", "quente", "resta", "reto", "rosa", "sempre", "sesta", "sexo",
    "toma", "trasantonte", "vella", "vello", "venres", "vosa", "voso", "xesta",
    "zorza",
]

GRAVES_TERMINACIONS_ABERTAS = [
    "ednoc", "aicne", "aine", "oine", "esne", "aino", "oino",
    "etnei", "etneu", "atneroc", "atneucnic", "atneses", "atnetes",
    "atnetio", "atnevon", "atnec", "otnec", "aicneu",
]

# agudas (oxytones) — open exceptions
AGUDAS_TERMINACIONS_ABERTAS = ["el", "ol", "en", "én", "oz", "ó"]

AGUDAS_PALABRAS_ABERTAS = [
    "cafés", "cempés", "chalés", "ciprés", "comités", "có", "cás",
    "don", "e", "fe", "fel", "gres", "ideal", "nós", "pés", "quer",
    "repousapés", "res", "rés", "sé", "través", "tés", "vés", "ó", "ós",
]

# Diacritic words that preserve open/close distinction
DIACRITICOS_OPOSICION = [
    "é", "ó", "és", "cé", "cés", "nós", "vós", "vén", "vés",
    "pré-sa", "bé-la", "bé-las", "ó-so", "cóm-pre",
    "pé-la", "tén", "té", "dé", "sé", "né", "só",
]


def _strip_stress(word: str) -> str:
    """Remove stress mark ^ from a word."""
    return word.replace('^', '')


def _word_lower(word: str) -> str:
    return _strip_stress(word).lower()


def _ends_with(word: str, suffixes: list[str]) -> bool:
    """Check if word (after removing trailing 's') ends with a suffix from list (reversed)."""
    w = _strip_stress(word).lower()
    bare = w.rstrip('s') if w.endswith('s') else w
    for sfx in suffixes:
        if bare.endswith(sfx):
            return True
    return False


def assign_timbre(word: str, lang: str = "gl") -> str:
    """Assign open (é/ó) or closed (e/o) timbre to stressed vowels.

    Operates on a word that already has stress marks (^).

    Args:
        word: Word with stress markers, e.g. "ca^-sa" or "ca-fé^"
        lang: Language code

    Returns:
        Word with open vowels marked as é/ó, e.g. "cá^-fe" or "ca^-fe"
    """
    if lang != "gl":
        return word  # Spanish timbre is simpler; skip for now

    # Only process words with stressed e or o
    if '^' not in word:
        return word

    # Already has open/close diacritic? Preserve it
    wl = _word_lower(word)
    for diac in DIACRITICOS_OPOSICION:
        if wl == diac:
            return word  # Keep as-is; diacritic already in original

    stress_pos = word.find('^')
    if stress_pos < 1:
        return word

    stressed_vowel = word[stress_pos - 1]
    if stressed_vowel not in ('e', 'o'):
        return word

    # Determine stress type: count syllables
    syllables = word.count('-') + 1
    if syllables <= 0:
        syllables = 1

    # Find which syllable from the end has stress
    stressed_syl_from_end = 0
    parts = word.split('-')
    char_count = 0
    for idx, part in enumerate(parts):
        if char_count + len(part) > stress_pos:
            stressed_syl_from_end = len(parts) - idx
            break
        char_count += len(part) + 1

    # aguda = last syllable (stressed_syl_from_end == 1)
    # grave = second-to-last (stressed_syl_from_end == 2)
    # esdrúxula = third-to-last (stressed_syl_from_end == 3)

    open_vowel = False

    if stressed_syl_from_end == 3:
        open_vowel = not _esdruxula_is_closed(word)
    elif stressed_syl_from_end == 2:
        open_vowel = not _grave_is_closed(word)
    else:
        open_vowel = _aguda_is_open(word)

    if open_vowel:
        # Replace e→é, o→ó
        if stressed_vowel == 'e':
            word = word[:stress_pos - 1] + chr(e_acentuada) + word[stress_pos:]
        elif stressed_vowel == 'o':
            word = word[:stress_pos - 1] + chr(o_acentuada) + word[stress_pos:]

    return word


def _esdruxula_is_closed(word: str) -> bool:
    """Check if an esdrúxula word has closed e/o."""
    wl = _word_lower(word)
    if _ends_with(word, ESDR_TERMINACIONS_PECHADAS):
        return True
    if wl in ESDR_PALABRAS_PECHADAS:
        return True
    return False  # default: open


def _grave_is_closed(word: str) -> bool:
    """Check if a grave word has closed e/o."""
    wl = _word_lower(word)
    if wl in GRAVES_PALABRAS_ABERTAS:
        return False
    if wl in GRAVES_PALABRAS_PECHADAS:
        return True
    if _ends_with(word, GRAVES_TERMINACIONS_ABERTAS):
        return False
    if _ends_with(word, GRAVES_TERMINACIONS_PECHADAS):
        return True
    return False  # default: open for graves


def _aguda_is_open(word: str) -> bool:
    """Check if an aguda word has open e/o."""
    wl = _word_lower(word)
    if wl in AGUDAS_PALABRAS_ABERTAS:
        return True
    if _ends_with(word, AGUDAS_TERMINACIONS_ABERTAS):
        return True
    return False  # default: closed for agudas
