# tr-bm25

[English](README.md) | **Türkçe**

Türkçe için küçük, bağımlılıksız **BM25** arama motoru. Türkçe'nin
`İ/ı` tuzağını doğru yönetir, görünmez karakterleri temizler, olumsuzluk
sözcüklerini korur ve isteğe bağlı gövdeleme + ASCII toleransı sunar.

- Saf Python (3.10+), çekirdek bağımlılık yok
- `index` / `search` API'si ve `tr-bm25` komut satırı aracı
- `pip install .` / `pip wheel .` ile kurulabilir

## Kurulum

```bash
pip install .
# geliştirme için
pip install -e ".[dev]"
```

## Hızlı başlangıç

```python
from tr_bm25 import BM25

belgeler = [
    "Kargom 12 Mart'ta gelmedi.",
    "Kitaplar raflarda duruyor.",
    "Kargo takip numarası e-postayla gönderildi.",
]

indeks = BM25(belgeler)
for sonuc in indeks.search("kargo gelmedi"):
    print(sonuc.belge_id, round(sonuc.skor, 4), sonuc.metin)
```

`BM25Indeks`, `indeksle()` ve `ara()` aynı işlevin Türkçe adlı
kısayollarıdır:

```python
from tr_bm25 import ara, indeksle

indeks = indeksle(["kargo geldi", "kitap geldi"], k1=1.5, b=0.75)
sonuclar = ara(indeks, "kargo", k=5)
```

### API

| Ad | Açıklama |
| --- | --- |
| `BM25(belgeler=None, *, k1=1.5, b=0.75, isleyici=None)` | İndeks nesnesi |
| `BM25.index(belgeler)` | İndeksi sıfırlayıp kurar, `self` döner |
| `BM25.ekle(belge)` | Tek belge ekler, kimliğini döndürür |
| `BM25.search(sorgu, k=10, *, min_skor=0.0)` | `Sonuc` listesi döner |
| `BM25.idf(terim)` | Terimin IDF değeri |
| `BM25.belge_sayisi` / `BM25.ortalama_uzunluk` | İndeks istatistikleri |
| `OnIsleyici(...).jetonlar(metin)` | Metni indeks terimlerine çevirir |
| `jetona_ayir(metin)` | Normalleştirilmiş jetonlar |
| `KokBulucu().kok(jeton)` | Türkçe kök bulucu |

`Sonuc` alanları: `belge_id`, `skor`, `metin`.

Skorlama klasik Okapi BM25'dir:

```
idf(t)  = ln(1 + (N - df(t) + 0.5) / (df(t) + 0.5))
skor(d) = Σ_t idf(t) * f(t,d) * (k1 + 1)
          / (f(t,d) + k1 * (1 - b + b * |d| / avgdl))
```

## Metin hattı

Sıra önemlidir ve belge ile sorgu aynı hattan geçirilir:

```
metin -> görünmez karakter temizliği -> Türkçe küçültme
      -> düzeltme işareti katlama -> jetonlama
      -> durak süzme -> (gövdeleme) -> (ASCII tolerans anahtarı)
```

### Türkçe küçültme

`str.lower()` Türkçe için yanlıştır; `"İ".lower()` birleşik nokta üretir.
Bu paket `İ -> i`, `I -> ı` eşlemesini açıkça yapar ve NFC normalleştirmesi
uygular:

```python
from tr_bm25 import turkce_kucult

turkce_kucult("İSTANBUL")   # 'istanbul'
turkce_kucult("ISPARTA")    # 'ısparta'
turkce_kucult("I\u0307ZMİR")  # 'izmir' (ayrıştırılmış İ de çalışır)
```

`ı` ile `i` ayrı harflerdir: `kılıç` ve `kiliç` birincil anahtarda ayrı
kalır. Yalnızca **ASCII tolerans katmanı** bunları bilinçli olarak
`kilic` altında birleştirir.

### ASCII toleransı

`OnIsleyici(ascii_tolerans=True)` (varsayılan) her Türkçe harfli terimin
hemen ardından ASCII katlanmış ikincil anahtarı da üretir. Böylece Türkçe
klavyesi olmayan `sisli` sorgusu `şişli` belgesiyle eşleşir; birincil
anahtar (`şişli`) korunur.

```python
from tr_bm25 import OnIsleyici

OnIsleyici(durak=False, ascii_tolerans=False).jetonlar("Şişli")
# ['şişli']
OnIsleyici(durak=False, ascii_tolerans=True).jetonlar("Şişli")
# ['şişli', 'sisli']
```

### Durak kelimeler ve olumsuzluk

`değil`, `yok`, `asla`, `hiç` gibi sözcükler varsayılan olarak korunur;
"kargo değil" ile "kargo" aynı sorguya dönüşmez. Kapatmak için:

```python
OnIsleyici(olumsuzluk_koru=False).jetonlar("kargo değil")
# ['kargo']
```

Durak süzme gövdelemeden **önce** yapılır; böylece `için` sözcüğünün
gövdesi olan `iç` yanlışlıkla silinmez.

### Gövdeleme

Varsayılan gövdeleyici saf Python'dur ve deterministiktir:

```python
from tr_bm25 import KokBulucu, OnIsleyici

KokBulucu().kok("kitaplar")   # 'kitap'
KokBulucu().kok("gelmedi")    # 'gel'

OnIsleyici(kok=True).jetonlar("Kitaplar raflarda")
# ['kitap', 'raf']
```

PyStemmer gibi harici bir gövdeleyici kullanmak isterseniz:

```python
import Stemmer
kok_bulucu = KokBulucu(lambda j: Stemmer.stemWord(j))
on_isleyici = OnIsleyici(kok=True, kok_bulucu=kok_bulucu)
```

### Görünmez karakterler

Soft hyphen (`U+00AD`), word joiner (`U+2060`), BOM (`U+FEFF`),
zero-width space (`U+200B`) gibi karakterler silinir:

```python
from tr_bm25 import jetona_ayir

jetona_ayir("ke\u00adlim")      # ['kelim']
jetona_ayir("kitap\u2060lar")   # ['kitaplar']
jetona_ayir("\ufeffkargo")      # ['kargo']
```

## Komut satırı

```bash
tr-bm25 --help
tr-bm25 ara "kargo gelmedi" belgeler/*.txt
tr-bm25 ara --kok --adet 5 --json "kitaplar" belgeler/*.txt
cat belge.txt | tr-bm25 ara "kargo"
tr-bm25 jetonla "Kargom 12 Mart'ta gelmedi!"
```

Her dosya bir belge sayılır. Sonuçlar skora göre azalan sırada yazılır.
`--kok`, `--durak-yok`, `--olumsuzluk-yok`, `--ascii-yok` ve `--json`
seçenekleri arama ile jetonlama alt komutlarında ortaktır.

## Test ve paketleme

```bash
python -m pytest -q
pip wheel --no-cache-dir --no-deps .
```

## Lisans

MIT — bkz. [LICENSE](LICENSE).
