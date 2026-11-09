# tr-bm25

[English](README.md) | [Türkçe](README.tr.md)

A small, dependency-free **BM25** search engine for Turkish. It handles the
Turkish `İ/ı` pitfall correctly, strips invisible characters, keeps negation
words and offers optional stemming and ASCII tolerance.

- Pure Python (3.10+), no runtime dependencies
- `index` / `search` API and a `tr-bm25` command line tool
- Installable with `pip install .` or `pip wheel .`

## Installation

```bash
pip install .
# for development
pip install -e ".[dev]"
```

## Quick start

```python
from tr_bm25 import BM25

documents = [
    "Kargom 12 Mart'ta gelmedi.",
    "Kitaplar raflarda duruyor.",
    "Kargo takip numarası e-postayla gönderildi.",
]

index = BM25(documents)
for result in index.search("kargo gelmedi"):
    print(result.belge_id, round(result.skor, 4), result.metin)
```

`BM25Indeks`, `indeksle()` and `ara()` are Turkish-named shortcuts for the same
functionality:

```python
from tr_bm25 import ara, indeksle

index = indeksle(["kargo geldi", "kitap geldi"], k1=1.5, b=0.75)
results = ara(index, "kargo", k=5)
```

### API

| Name | Description |
| --- | --- |
| `BM25(belgeler=None, *, k1=1.5, b=0.75, isleyici=None)` | Index object |
| `BM25.index(belgeler)` | Resets and builds the index, returns `self` |
| `BM25.ekle(belge)` | Adds one document and returns its id |
| `BM25.search(sorgu, k=10, *, min_skor=0.0)` | Returns a list of `Sonuc` |
| `BM25.idf(terim)` | IDF value of a term |
| `BM25.belge_sayisi` / `BM25.ortalama_uzunluk` | Index statistics |
| `OnIsleyici(...).jetonlar(metin)` | Converts text into index terms |
| `jetona_ayir(metin)` | Normalized tokens |
| `KokBulucu().kok(jeton)` | Turkish stemmer |

`Sonuc` fields: `belge_id`, `skor`, `metin`.

Scoring is classic Okapi BM25:

```
idf(t)  = ln(1 + (N - df(t) + 0.5) / (df(t) + 0.5))
score(d) = sum_t idf(t) * f(t,d) * (k1 + 1)
           / (f(t,d) + k1 * (1 - b + b * |d| / avgdl))
```

## Text pipeline

Order matters, and documents and queries go through the same pipeline:

```
text -> invisible character removal -> Turkish lowercasing
     -> circumflex folding -> tokenization
     -> stopword filtering -> (stemming) -> (ASCII tolerance key)
```

### Turkish lowercasing

`str.lower()` is wrong for Turkish: `"İ".lower()` produces a combining dot. This
package maps `İ -> i` and `I -> ı` explicitly and applies NFC normalization:

```python
from tr_bm25 import turkce_kucult

turkce_kucult("İSTANBUL")     # 'istanbul'
turkce_kucult("ISPARTA")      # 'ısparta'
turkce_kucult("I\u0307ZMİR")  # 'izmir' (a decomposed İ works too)
```

`ı` and `i` are different letters: `kılıç` and `kiliç` stay apart in the
primary key. Only the **ASCII tolerance layer** merges them on purpose, under
`kilic`.

### ASCII tolerance

`OnIsleyici(ascii_tolerans=True)` (the default) emits an ASCII-folded secondary
key right after every term that contains Turkish letters. A query typed without
a Turkish keyboard (`sisli`) therefore matches a document containing `şişli`;
the primary key (`şişli`) is kept.

```python
from tr_bm25 import OnIsleyici

OnIsleyici(durak=False, ascii_tolerans=False).jetonlar("Şişli")
# ['şişli']
OnIsleyici(durak=False, ascii_tolerans=True).jetonlar("Şişli")
# ['şişli', 'sisli']
```

### Stopwords and negation

Words such as `değil`, `yok`, `asla` and `hiç` are kept by default, so
"kargo değil" does not collapse into the same query as "kargo". To turn this off:

```python
OnIsleyici(olumsuzluk_koru=False).jetonlar("kargo değil")
# ['kargo']
```

Stopword filtering runs **before** stemming, so `iç`, the stem of `için`, is not
removed by mistake.

### Stemming

The default stemmer is pure Python and deterministic:

```python
from tr_bm25 import KokBulucu, OnIsleyici

KokBulucu().kok("kitaplar")   # 'kitap'
KokBulucu().kok("gelmedi")    # 'gel'

OnIsleyici(kok=True).jetonlar("Kitaplar raflarda")
# ['kitap', 'raf']
```

To use an external stemmer such as PyStemmer:

```python
import Stemmer
stemmer = KokBulucu(lambda token: Stemmer.stemWord(token))
preprocessor = OnIsleyici(kok=True, kok_bulucu=stemmer)
```

### Invisible characters

Characters such as soft hyphen (`U+00AD`), word joiner (`U+2060`), BOM
(`U+FEFF`) and zero-width space (`U+200B`) are removed:

```python
from tr_bm25 import jetona_ayir

jetona_ayir("ke\u00adlim")      # ['kelim']
jetona_ayir("kitap\u2060lar")   # ['kitaplar']
jetona_ayir("\ufeffkargo")      # ['kargo']
```

## Command line

```bash
tr-bm25 --help
tr-bm25 ara "kargo gelmedi" documents/*.txt
tr-bm25 ara --kok --adet 5 --json "kitaplar" documents/*.txt
cat document.txt | tr-bm25 ara "kargo"
tr-bm25 jetonla "Kargom 12 Mart'ta gelmedi!"
```

Every file counts as one document. Results are printed in descending score
order. The options `--kok` (stemming), `--durak-yok` (no stopwords),
`--olumsuzluk-yok` (do not keep negation), `--ascii-yok` (no ASCII tolerance)
and `--json` are shared by the search and tokenize subcommands.

## Tests and packaging

```bash
python -m pytest -q
pip wheel --no-cache-dir --no-deps .
```

## License

MIT, see [LICENSE](LICENSE).
