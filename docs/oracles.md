# The two oracles

pycotovia is verified against the Cotovia C binary. There are two builds of
that binary, both first class, and each one defines a different pycotovia
behaviour.

| Build | Source | pycotovia | Role |
|-------|--------|-----------|------|
| **fixed** | upstream + `cotovia-mirror` PR #2 and PR #4 | default | The reference. Every headline number in `docs/parity.md` is measured against this build. |
| **pristine** | upstream `cotovia-mirror` HEAD | `keep_bugs=True` | Stock Cotovia, defects included. For byte-compatibility with anything already built on the shipped binary. |

Crossing the pair is meaningless. Default pycotovia is not trying to match the
pristine build, and `keep_bugs=True` is not trying to match the fixed build.

```python
from pycotovia import phonemize

phonemize("fui cuido", tra=2)                   # 'fu^j ku^jDo'  — fixed build
phonemize("fui cuido", tra=2, keep_bugs=True)   # 'fwi^ kwi^Do'  — stock binary
```

## Building both

```bash
# pristine — stock upstream, no local changes
git clone https://github.com/TigreGotico/cotovia-mirror cotovia-pristine
make -C cotovia-pristine/src/cotovia

# fixed — upstream plus the two adjudicated fixes
git clone https://github.com/TigreGotico/cotovia-mirror
cd cotovia-mirror
gh pr checkout 2 && git checkout -            # or apply the two-line patch
gh pr checkout 4 && git checkout -
make -C src/cotovia
```

Both fixes touch only `src/cotovia/sil_acen.cpp`, four lines in total.

Scoring against each:

```bash
python3 tools/parity_harness.py corpus.txt --oracle fixed
python3 tools/parity_harness.py corpus.txt --oracle pristine
python3 tools/parity_harness.py corpus.txt --oracle both     # + the divergence table
```

## What separates the two builds

Measured on 5000 Galician Wikipedia sentences (48024 word tokens). The list is
exhaustive: these are **all** the differences between the two binaries.

| Mode | Sentences differing | Words differing |
|------|---------------------|-----------------|
| `-t0` | 515/5000 | 527/48024 (1.097%) |
| `-t1` | 515/5000 | 527/48024 (1.097%) |
| `-t2` | 515/5000 | 527/48024 (1.097%) |
| `-t3` | 16/5000 | 18/44016 (0.041%) |

Every differing token, at `-t0`:

| fixed | pristine | count | Fix |
|-------|----------|-------|-----|
| `E` | `e` | 508 | PR #4 |
| `lujs` | `lwis` | 4 | PR #2 |
| `tuj` | `twi` | 3 | PR #2 |
| `rrujT` | `rrwiT` | 2 | PR #2 |
| `loujs` | `lowis` | 1 | PR #2 |
| `fukuj` | `fukwi` | 1 | PR #2 |
| `mujmne` | `mwimne` | 1 | PR #2 |
| `rrotSrujDe` | `rrotSrwiDe` | 1 | PR #2 |
| `nuj` | `nwi` | 1 | PR #2 |
| `lujxi` | `lwixi` | 1 | PR #2 |
| `pujDo` | `pwiDo` | 1 | PR #2 |
| `mawritsujs` | `mawritswis` | 1 | PR #2 |
| `mujskas` | `mwiskas` | 1 | PR #2 |

Fourteen classes, and no others. At `-t3` only the PR #2 classes remain: PR #4
contributes nothing there, because the prosodic stage opens `é` anyway.

## The case for each fix

Both fixes are meant to be upstreamable. The pull requests on
`TigreGotico/cotovia-mirror` are marked reference-only because that repository
is a mirror, not because the defects are in doubt.

### PR #2 — `(*p-2)` should be `p[-2]` in `aguda()` and `grave()`

`src/cotovia/sil_acen.cpp`:

```c
if (!((*(p-1)=='u') && p>palabra+1 && ( (*p-2)=='q' || (*p-2)=='g' ) ))
   p--;
```

**What the guard is for.** `p` points at the vowel that carries the stress.
When that vowel is `i` or `u` and the letter before it is also a vowel, the
stress belongs on the first of the two, so the code steps back with `p--`. The
guard suppresses that step in one case: the silent `u` of the digraphs `qu`
and `gu`. In *guiar* or *quiosco* the `u` is not a nucleus and cannot take the
stress, so `p` must stay on the `i`.

**What the code actually does.** `*p-2` parses as `(*p)-2`: the character code
of the current vowel, minus two. The switch that reaches this line has only
the cases `'i'` and `'u'`. For `'i'` (0x69) the expression is 0x67, which is
`'g'`, so the test succeeds unconditionally. The guard therefore fires for
*every* `ui` sequence, whether or not a `q` or `g` precedes it.

**Why this cannot be intended.** Three independent reasons:

1. The bounds check `p>palabra+1` guards a read at `p[-2]`. There is no other
   reason to require that `p` is at least two characters into the word. If the
   author had meant `(*p)-2`, an expression that reads no memory, the bounds
   check would be dead code sitting between two operands of the same `&&`.
2. The same expression reads `*(p-1)` correctly on the same line, so the
   parenthesised idiom was clearly known to the author.
3. The condition is only reached after `*(p-1)=='u'` succeeds, that is, "the
   previous letter is a `u`". The only question left to ask is whether that
   `u` follows a `q` or a `g`. `(*p)-2` does not answer it, and comparing a
   character-arithmetic result against a letter is meaningless.

**Why the fixed behaviour is the linguistically correct one.** In Galician the
sequence `ui` outside `qu`/`gu` is a falling diphthong: the nucleus is the
`u` and the `i` is the semivowel, /uj/. This is what the RAG/ILG *Normas
ortográficas e morfolóxicas do idioma galego* prescribe, and it is why *fui*,
*cuido*, *Luís*, *Muíños* and *Ruíz* are stressed on the `u`.

| Word | fixed | pristine | Correct? |
|------|-------|----------|----------|
| `fui` | `fu^j` | `fwi^` | fixed — falling /uj/, stress on `u` |
| `cuido` | `ku^jDo` | `kwi^Do` | fixed — /ˈkujðo/ |
| `Luis` | `lu^js` | `lwi^s` | fixed — /ˈlujs/ |
| `guiar` | `gja^r` | `gja^r` | both — the guard does its real job here |
| `lingua` | `li^Ngwa` | `li^Ngwa` | both |

The stock output `fwi`, `kwiDo` and `lwis` is the *Spanish* rising diphthong
/wi/. Cotovia already handles Spanish through a separate rule table, so
importing the Spanish pattern into the Galician path is not a dialect choice;
it is the guard misfiring. Note that the `qu`/`gu` cases are unaffected by the
fix, which is the point: the fix restores the guard to the words it was
written for, and removes it from the words it was never meant to touch.

### PR #4 — off-by-one in `diacritico_dif_aberta_pechada()`

```c
const char *diacriticos_oposicion_aberta_pechada[]={"é","ó","ós",
   "có","cós","nós","vós","vén","vés","pré-sa","bó-la","bó-las","ó-so",
   "cóm-pre","pó-la","tén","té","dó","sé","nó","só","\0"};
...
cont=0;
while (*diacriticos_oposicion_aberta_pechada[cont++]!=0 ){
   if (strcmp(diacriticos_oposicion_aberta_pechada[cont],pal_entrada)==0){
```

`cont++` sits in the guard, so the guard tests entry N while the body compares
entry N+1. Entry 0, `"é"`, is never compared. The `"\0"` terminator at entry 21
is compared instead, and can never match.

**Why this cannot be intended.**

1. `"é"` is in the data. The author wrote it into the table; the loop cannot
   reach it. Code and data disagree, and the data is the statement of intent.
2. Exactly one real element is lost and exactly one dead comparison is gained.
   That is the arithmetic signature of the `cont++` placement, not a policy
   choice. A deliberate exclusion would have removed the entry.
3. Every sibling entry is reachable and works: `ó`, `ós`, `nós`, `vós`, `vén`,
   `vés`, `só`, `ó-so`, `pó-la`, `cóm-pre`. Verified against the binary — the
   entries at index 1 and index 20 both match, and only index 0 does not.

**What the table is for.** Galician contrasts open and closed mid vowels
phonemically: /ɛ/ against /e/, /ɔ/ against /o/. The RAG *acento diacrítico*
marks that contrast rather than stress, and this table is Cotovia's
implementation of it. The pairs it exists to separate include:

| Open | Closed | Contrast |
|------|--------|----------|
| `é` /ɛ/ "is" | `e` /e/ "and" | **the excluded entry** |
| `ós` /ɔs/ "to the" | `os` /os/ "the" | reached |
| `óso` /ˈɔso/ "bone" | `oso` /ˈoso/ "bear" | reached |
| `póla` /ˈpɔla/ "branch" | `pola` /ˈpola/ "hen, by the" | reached |
| `vés` /bɛs/ "you come" | `ves` /bes/ "you see" | reached |

`é` against `e` is the highest-frequency minimal pair of the set: the copula
against the coordinating conjunction. Losing it is losing the case the table
was most obviously written for.

**Cotovia already disagrees with itself here.** At `-t3` the binary emits `E^`
for `é`, because the prosodic stage assigns verb timbre and *ser* is a verb.
So the same binary produces closed `e^` at `-t0..-t2` and open `E^` at `-t3`
for the same word. The fix removes that internal inconsistency; it does not
introduce a new behaviour. This is the strongest reason to take it upstream:

```
$ echo "el é o meu irmán." | ./bin/cotovia -St2lgl     # stock
e^l e^ o^ me^w ir-ma^N
$ echo "el é o meu irmán." | ./bin/cotovia -St3lgl     # stock, same binary
#%pausa 50%# %prop 245% e^l E^ o me^w ir-ma^N #%pausa 800%#
```

**Cost.** 508 tokens in 5000 sentences at `-t0..-t2`, and nothing at `-t3`.

---
[← Parity](parity.md) · [Home](../README.md)
