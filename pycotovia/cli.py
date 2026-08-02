"""Command-line interface for pycotovia."""

import sys
from .phonemize import Phonemizer
from .alphabets import ALPHABETS, NATIVE_ALPHABET


def main():
    lang = "gl"
    alphabet = NATIVE_ALPHABET
    args = sys.argv[1:]
    while args and args[0].startswith('-'):
        flag = args.pop(0)
        if flag == '-l' and args:
            lang = args.pop(0)
        elif flag in ('-a', '--alphabet') and args:
            alphabet = args.pop(0)
        elif flag == '--help':
            print(
                "Usage: python -m pycotovia [-l gl|es] [-a alphabet] < input.txt\n"
                f"Alphabets: {', '.join(ALPHABETS)}",
                file=sys.stderr,
            )
            sys.exit(0)

    p = Phonemizer(lang)
    try:
        for line in sys.stdin:
            line = line.rstrip('\n').rstrip('\r')
            result = p.phonemize(line, alphabet=alphabet)
            sys.stdout.write(result + '\n')
            sys.stdout.flush()
    except (BrokenPipeError, IOError):
        pass


if __name__ == "__main__":
    main()
