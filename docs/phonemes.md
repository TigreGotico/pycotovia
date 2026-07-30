# Phoneme inventory

Complete mapping from Cotovia phoneme symbols to IPA, with English pronunciation guides and examples.

## Consonants

| Cotovia | IPA | Name | English approx. | Example word |
|---------|-----|------|-----------------|--------------|
| b | /b/ | voiced bilabial plosive | **b**oy | banco |
| d | /d/ | voiced alveolar plosive | **d**og | dado |
| g | /ɡ/ | voiced velar plosive | **g**o | gato |
| p | /p/ | voiceless bilabial plosive | **p**en | perro |
| t | /t/ | voiceless alveolar plosive | **t**op | toro |
| k | /k/ | voiceless velar plosive | **c**at | casa |
| f | /f/ | voiceless labiodental fricative | **f**ish | foto |
| s | /s/ | voiceless alveolar fricative | **s**un | sol |
| x | /x/ | voiceless velar fricative | lo**ch** (Scottish) | juego, gente |
| G | /ɣ/ | voiced velar fricative | (no English equivalent) | amigo, lago |
| B | /β/ | voiced bilabial fricative | (no English equivalent) | cabo, lava |
| D | /ð/ | voiced dental fricative | **th**en | nada, cada |
| T | /θ/ | voiceless dental fricative | **th**ink | zapato, cena |
| S | /ʃ/ | voiceless postalveolar fricative | **sh**ip | xaneiro (Galician) |
| J | /ɲ/ | palatal nasal | ca**ny**on | niño, año |
| N | /ŋ/ | velar nasal | si**ng** | cinco, tango |
| Z | /ʎ/ | palatal lateral approximant | mi**lli**on | llingua (Galician) |
| n | /n/ | alveolar nasal | **n**o | nuevo |
| m | /m/ | bilabial nasal | **m**an | mesa |
| l | /l/ | alveolar lateral approximant | **l**ight | luz |
| r | /ɾ/ | alveolar tap | (no English equivalent) | cara, pero |
| rr | /r/ | alveolar trill | (rolled R) | perro, carro |
| j | /j/ | palatal approximant | **y**es | hielo, tierra |
| w | /w/ | labial-velar approximant | **w**et | hueso, cuido |
| tS | /tʃ/ | voiceless postalveolar affricate | **ch**urch | chico, coche |
| ts | /ts/ | voiceless alveolar affricate | ca**ts** | (rare in Galician/Spanish) |
| c | /ts/ | same as ts | ca**ts** | (rare) |
| ts` | /ts/ | same as ts | ca**ts** | (rare) |
| s` | /ʃ/ | same as S | **sh**ip | (variant) |
| gj | /ɡʝ/ | velar + palatal | (no English equivalent) | (rare) |
| jj | /ʝʝ/ | geminate palatal | (no English equivalent) | (rare) |
| L | /ʎ/ | same as Z | mi**lli**on | (variant) |

## Vowels

| Cotovia | IPA | Name | English approx. | Example word |
|---------|-----|------|-----------------|--------------|
| a | /a/ | open central unrounded | **fa**ther | casa, cara |
| e | /e/ | close-mid front unrounded | m**e**t | mesa, cena |
| E | /ɛ/ | open-mid front unrounded | b**e**t | (Galician open e, stressed) |
| i | /i/ | close front unrounded | f**ee**t | sí, día |
| o | /o/ | close-mid back rounded | b**oa**t | ola, solo |
| O | /ɔ/ | open-mid back rounded | c**au**ght | (Galician open o, stressed) |
| u | /u/ | close back rounded | b**oo**t | uno, luz |

## Special symbols

| Symbol | Meaning | Usage |
|--------|---------|-------|
| # | silence/pause | marks phrase boundaries |
| % | silence (variant) | alternative pause marker |
| ^ | stress marker | placed after the stressed vowel |
| - | syllable separator | placed between syllables |

## Notes on allophones

### Softened consonants (spirantization)

In Galician and Spanish, voiced stops /b/, /d/, /g/ become fricatives between vowels:

- `b` → /b/ at word start, /β/ between vowels (written as `B` in Cotovia)
- `d` → /d/ at word start, /ð/ between vowels (written as `D` in Cotovia)
- `g` → /ɡ/ at word start, /ɣ/ between vowels (written as `G` in Cotovia)

Examples:
- `banco` → `b` (word-initial, /b/)
- `cabo` → `B` (between vowels, /β/)
- `dado` → `d` (word-initial, /d/)
- `nada` → `D` (between vowels, /ð/)
- `gato` → `g` (word-initial, /ɡ/)
- `amigo` → `G` (between vowels, /ɣ/)

### Galician vs Spanish

| Sound | Galician | Spanish | Example |
|-------|----------|---------|---------|
| x | /ʃ/ (sh) | /ks/ (x) | xaneiro (gl) vs México (es) |
| z | /θ/ (th) | /θ/ or /s/ | zapato |
| c (e,i) | /θ/ (th) | /θ/ or /s/ | cena |
| g (e,i) | /x/ (h) | /x/ (h) | gente |
| ll | /ʎ/ (lli) | /ʝ/ (y) or /ʎ/ | llingua (gl) vs lluvia (es) |
| r (single) | /ɾ/ (tap) | /ɾ/ (tap) | cara |
| rr | /r/ (roll) | /r/ (roll) | perro |

### Stress and vowel quality

In Galician (not Spanish), stressed `e` and `o` can be open or closed:

- Closed e: /e/ (as in "met") → written as `e` in Cotovia
- Open e: /ɛ/ (as in "bet") → written as `E` in Cotovia
- Closed o: /o/ (as in "boat") → written as `o` in Cotovia
- Open o: /ɔ/ (as in "caught") → written as `O` in Cotovia

Whether a vowel is open or closed depends on the surrounding consonants and the word. The Cotovia binary can compute this, but pycotovia does NOT apply it in transcription mode: this is intentional and matches the binary's `-t0` mode.

### The silent u

In Spanish and Galician, `q` is always followed by `u` (silent), and `g` before `e` or `i` is also followed by silent `u`:

- `que` → /ke/ (silent u)
- `qui` → /ki/ (silent u)
- `gue` → /ge/ (silent u)
- `gui` → /gi/ (silent u)
- `gua` → /gwa/ (u is pronounced!)
- `güe` → /gwe/ (u is pronounced due to diaeresis)

This is why the `q/g` guard exists in the stress logic: when shifting stress from `i` to `u`, we must NOT shift if the `u` is silent.

## Diphthongs and triphthongs

Diphthongs and triphthongs are sequences of vowels pronounced as a single syllable. They are not separate phonemes in the inventory: they are combinations of the vowels above.

Examples:
- `ai` → /ai/ (aigüe → /aj.ɣe/)
- `ei` → /ei/ (reina → /rei.na/)
- `oi` → /oi/ (oigo → /oi.ɣo/)
- `au` → /au/ (auto → /au.to/)
- `eu` → /eu/ (europa → /eu.ɾo.pa/)
- `ou` → /ou/ (ouro → /ou.ɾo/)
- `ui` → /ui/ (bui → /buj/)
- `iu` → /iu/ (viuda → /bju.ða/)
- `uia` → /uja/ (guia → /gja/)
- `uie` → /uje/ (quiebra → /kje.βɾa/)
- `uio` → /ujo/ (guion → /gjon/)

## Cotovia → IPA mapping code

The mapping is implemented in `pycotovia/phonemes.py`:

```python
COTOVIA2IPA = {
    "b": "b", "B": "β", "d": "d", "D": "ð",
    "g": "ɡ", "G": "ɣ", "p": "p", "t": "t",
    "k": "k", "f": "f", "s": "s", "S": "ʃ",
    "x": "x", "T": "θ", "J": "ɲ", "N": "ŋ",
    "Z": "ʎ", "L": "ʎ", "j": "j", "w": "w",
    "tS": "tʃ", "ts": "ts", "ts`": "ts",
    "rr": "r", "r": "ɾ", "n": "n", "m": "m",
    "l": "l", "a": "a", "e": "e", "E": "ɛ",
    "i": "i", "o": "o", "O": "ɔ", "u": "u",
}
```

## Usage

```python
from pycotovia import cotovia_to_ipa

# Single word
cotovia_to_ipa("gerra")     # "ɣɛra"
cotovia_to_ipa("kasa")      # "kasa"
cotovia_to_ipa("tSa")       # "tʃa"
cotovia_to_ipa("MeSiko")    # "meʃiko"
```

## See also

- `docs/phonetics.md`: phonetics background for non-speakers
- `docs/algorithm.md`: how the rules produce these phonemes
- `docs/parity.md`: verification that pycotovia matches the binary

---
[← Phonetics](phonetics.md) · [Home](../README.md) · [Exceptions →](exceptions.md)
