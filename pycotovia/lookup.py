"""Cotovia's word-list searches — ports of the two lookup functions in
``trat_fon.cpp``.

These are binary searches. That matters more than it looks: several of the
lists they search are not fully sorted, so some entries are unreachable and
the binary silently never matches them. Replacing the search with a linear
scan would "find" those entries and change the transcription of real words
away from what the binary produces.

Comparison is ``strcmp`` over Latin-1 bytes, so entries and words are encoded
before comparing rather than compared as Python strings.
"""


def _encode(s: str) -> bytes:
    return s.encode("latin-1", "replace")


def _midpoint(lo: int, hi: int) -> int:
    # C integer division truncates toward zero; Python's // floors.
    return int((lo + hi) / 2)


def buscar_palabra(lista: tuple[str, ...], pal: str) -> int:
    """Exact match — port of ``comprobar_en_lista_de_palabras()``.

    Returns the index, or -1.
    """
    if not lista:
        return -1
    word = _encode(pal)
    lim_inferior, lim_superior = 0, len(lista) - 1
    while True:
        punto_medio = _midpoint(lim_superior, lim_inferior)
        if not 0 <= punto_medio < len(lista):
            return -1
        entry = _encode(lista[punto_medio])
        if word > entry:
            if lim_inferior >= lim_superior:
                return -1
            lim_inferior = punto_medio + 1
        elif word < entry:
            if lim_inferior >= lim_superior:
                return -1
            lim_superior = punto_medio - 1
        else:
            return punto_medio


def buscar_inicio(lista: tuple[str, ...], pal: str,
                  inverso: bool = False, limite: int | None = None) -> int:
    """Prefix match — port of ``comprobar_en_lista_de_inicio_de_palabras()``.

    Binary search first, then a truncated comparison at the landing point and
    a backward scan while the first character still agrees.

    With ``inverso`` the word is reversed before searching, which turns the
    prefix match into a suffix match. The list entries are already stored
    reversed in that case (``EN_DICCIONARIO_INVERSO``).

    ``limite`` restricts the search to the first N entries. The verb analyser
    uses it to look for shorter endings after it has found a longer one:
    ``gbm::busca()`` clamps the list to ``tamanio`` the same way.

    Returns the index, or -1.
    """
    if not lista:
        return -1
    if limite is not None:
        lista = lista[:max(limite, 0)]
        if not lista:
            return -1
    word = _encode(pal[::-1] if inverso else pal)

    lim_inferior, lim_superior = 0, len(lista) - 1
    punto_medio = 0
    while True:
        punto_medio = _midpoint(lim_superior, lim_inferior)
        if not 0 <= punto_medio < len(lista):
            return -1
        entry = _encode(lista[punto_medio])
        if word > entry:
            if lim_inferior >= lim_superior:
                break
            lim_inferior = punto_medio + 1
        elif word < entry:
            if lim_inferior >= lim_superior:
                break
            lim_superior = punto_medio - 1
        else:
            return punto_medio

    # Compare the beginnings: trim the word to the entry's length.
    while True:
        entry = _encode(lista[punto_medio])
        if word[:len(entry)] == entry:
            return punto_medio
        if punto_medio == 0:
            return -1
        if word[:1] != _encode(lista[punto_medio - 1])[:1]:
            return -1
        punto_medio -= 1
