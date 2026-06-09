#!/usr/bin/env python3
"""Batch processing example — read words from a file and write phonemes."""

import sys
import pycotovia

# Example: python phrase_processing.py words.txt phonemes.txt gl

def main():
    if len(sys.argv) < 3:
        print("Usage: python phrase_processing.py <input.txt> <output.txt> [lang]", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    lang = sys.argv[3] if len(sys.argv) > 3 else "gl"

    p = pycotovia.Phonemizer(lang=lang)

    with open(input_file, encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip()]

    with open(output_file, "w", encoding="utf-8") as f:
        for word in words:
            phonemes = p.phonemize(word)
            f.write(f"{word}\t{phonemes}\n")

    print(f"Processed {len(words)} words → {output_file}")


if __name__ == "__main__":
    main()
