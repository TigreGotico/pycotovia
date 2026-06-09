#!/usr/bin/env python3
"""Basic usage examples for pycotovia."""

import pycotovia

# --- Single words ---
print("Galician:")
for word in ["casa", "cantar", "guerra", "guia", "quilo", "seguir"]:
    print(f"  {word:10} → {pycotovia.phonemize(word, lang='gl')}")

print("\nSpanish:")
for word in ["casa", "cantar", "México", "examen", "guitarra"]:
    print(f"  {word:10} → {pycotovia.phonemize(word, lang='es')}")

# --- Phrases ---
print("\n--- Phrases ---")
print(f"Ola, como estás? → {pycotovia.phonemize('Ola, como estás?', lang='gl')}")
print(f"Hola, ¿cómo estás? → {pycotovia.phonemize('Hola, ¿cómo estás?', lang='es')}")

# --- Output levels ---
print("\n--- Output levels ---")
word = "guerra"
for tra in [1, 2, 3, 4]:
    print(f"  tra={tra}: {pycotovia.phonemize(word, lang='gl', tra=tra)!r}")

# --- IPA ---
print("\n--- IPA ---")
for word in ["casa", "guerra", "quilo"]:
    cot = pycotovia.phonemize(word, lang='gl')
    ipa = pycotovia.cotovia_to_ipa(cot)
    print(f"  {word:10} {cot:10} → {ipa}")
