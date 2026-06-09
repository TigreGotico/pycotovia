#!/usr/bin/env python3
"""Spanish-specific examples showing differences from Galician."""

import pycotovia

# Spanish x → ks
print("Spanish 'x' vs Galician 'x':")
for word in ["México", "examen", "éxito", "exilio"]:
    es = pycotovia.phonemize(word, lang="es")
    gl = pycotovia.phonemize(word, lang="gl")
    print(f"  {word:10} es={es:15} gl={gl}")

# Spanish w → gu
print("\nSpanish 'w' words:")
for word in ["sandwich", "hawaiano", "whisky"]:
    print(f"  {word:10} → {pycotovia.phonemize(word, lang='es')}")

# Open/closed e/o — both languages handle these in the same way
print("\nOpen/closed e/o (same in both languages):")
for word in ["cafe", "publico", "economico"]:
    es = pycotovia.phonemize(word, lang="es", tra=3)
    gl = pycotovia.phonemize(word, lang="gl", tra=3)
    print(f"  {word:10} es={es:20} gl={gl}")
