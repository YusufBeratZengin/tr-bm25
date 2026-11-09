"""Küçük ölçekli BM25 indeksi ve sorgulama API'si.

Projenin adını karşılayan çekirdek modül. Bağımlılık yoktur; belgeler
:class:`~tr_bm25.tokenize.OnIsleyici` hattından geçirilir (Türkçe
küçültme, görünmez karakter temizliği, durak süzme, isteğe bağlı
gövdeleme ve ASCII toleransı).

BM25 skoru, klasik Okapi formülüdür::

    idf(t) = ln(1 + (N - df(t) + 0.5) / (df(t) + 0.5))
    skor(d, q) = Σ_t idf(t) * f(t,d) * (k1 + 1)
                 / (f(t,d) + k1 * (1 - b + b * |d| / avgdl))

>>> indeks = BM25(["kargo bugün geldi", "kitaplar raflarda"])
>>> [s.belge_id for s in indeks.search("kargo")]
[0]
>>> round(indeks.idf("kargo"), 4)
0.6931
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from .tokenize import OnIsleyici

__all__ = ["BM25", "BM25Indeks", "Sonuc", "ara", "indeksle"]


@dataclass(frozen=True, slots=True)
class Sonuc:
    """Tek bir arama sonucu.

    Attributes:
        belge_id: Belgenin indeksteki sıfır tabanlı konumu.
        skor: BM25 skoru (büyük olan daha alakalı).
        metin: Belgenin özgün metni.
    """

    belge_id: int
    skor: float
    metin: str


class BM25:
    """Türkçe metinler için BM25 indeksi.

    Args:
        belgeler: İsteğe bağlı başlangıç belgeleri. Verilirse ``index``
            hemen çağrılır.
        k1: Terim frekansı doygunluk parametresi (varsayılan 1.5).
        b: Belge uzunluğu normalizasyonu (varsayılan 0.75).
        isleyici: Özel :class:`~tr_bm25.tokenize.OnIsleyici`; verilmezse
            ``OnIsleyici(kok=False, durak=True)`` kullanılır.

    >>> indeks = BM25()
    >>> _ = indeks.index(["kargo geldi", "kargo gitti", "kitap geldi"])
    >>> [(s.belge_id, round(s.skor, 3)) for s in indeks.search("kargo")]
    [(0, 0.47), (1, 0.47)]
    """

    def __init__(
        self,
        belgeler: Iterable[str] | None = None,
        *,
        k1: float = 1.5,
        b: float = 0.75,
        isleyici: OnIsleyici | None = None,
    ) -> None:
        if k1 <= 0:
            raise ValueError("k1 pozitif olmalı")
        if not 0.0 <= b <= 1.0:
            raise ValueError("b 0 ile 1 arasında olmalı")
        self.k1 = float(k1)
        self.b = float(b)
        self.isleyici = isleyici if isleyici is not None else OnIsleyici(kok=False, durak=True)
        self._belgeler: list[str] = []
        self._terim_frekanslari: list[Counter[str]] = []
        self._uzunluklar: list[int] = []
        self._belge_frekansi: Counter[str] = Counter()
        self._idf: dict[str, float] = {}
        self._ortalama_uzunluk = 0.0
        if belgeler is not None:
            self.index(belgeler)

    # ------------------------------------------------------------------ #
    # İndeksleme
    # ------------------------------------------------------------------ #
    def index(self, belgeler: Iterable[str]) -> BM25:
        """İndeksi sıfırlayıp verilen belgelerle yeniden kurar.

        Args:
            belgeler: Belge metinleri. Her öğe bir belgedir.

        Returns:
            ``self`` (zincirleme için).

        Raises:
            TypeError: Bir öğe ``str`` değilse.
        """
        yeni_belgeler: list[str] = []
        terim_frekanslari: list[Counter[str]] = []
        uzunluklar: list[int] = []
        belge_frekansi: Counter[str] = Counter()

        for belge in belgeler:
            if not isinstance(belge, str):
                raise TypeError(f"belge str olmalı, {type(belge).__name__} verildi")
            jetonlar = self.isleyici.jetonlar(belge)
            tf = Counter(jetonlar)
            yeni_belgeler.append(belge)
            terim_frekanslari.append(tf)
            uzunluklar.append(len(jetonlar))
            belge_frekansi.update(tf.keys())

        self._belgeler = yeni_belgeler
        self._terim_frekanslari = terim_frekanslari
        self._uzunluklar = uzunluklar
        self._belge_frekansi = belge_frekansi
        n = len(yeni_belgeler)
        self._ortalama_uzunluk = (sum(uzunluklar) / n) if n else 0.0
        self._idf = {terim: self._idf_hesapla(terim, n) for terim in belge_frekansi}
        return self

    def ekle(self, belge: str) -> int:
        """Tek belge ekler ve yeni belgenin kimliğini döndürür.

        IDF değerleri belge sayısına bağlı olduğu için indeks yeniden
        hesaplanır; küçük ölçekli kullanım için kabul edilebilir.
        """
        if not isinstance(belge, str):
            raise TypeError(f"belge str olmalı, {type(belge).__name__} verildi")
        belgeler = [*self._belgeler, belge]
        self.index(belgeler)
        return len(belgeler) - 1

    # ------------------------------------------------------------------ #
    # Sorgulama
    # ------------------------------------------------------------------ #
    def idf(self, terim: str) -> float:
        """Bir terimin IDF değeri; indekste yoksa da pozitif döner."""
        if terim in self._idf:
            return self._idf[terim]
        return self._idf_hesapla(terim, self.belge_sayisi)

    def _idf_hesapla(self, terim: str, n: int) -> float:
        df = self._belge_frekansi.get(terim, 0)
        return math.log(1.0 + (n - df + 0.5) / (df + 0.5))

    def search(self, sorgu: str, k: int = 10, *, min_skor: float = 0.0) -> list[Sonuc]:
        """Sorguya göre belgeleri BM25 skoruyla sıralar.

        Args:
            sorgu: Sorgu metni; belgelerle aynı hattan geçirilir.
            k: Döndürülecek en fazla sonuç sayısı.
            min_skor: Bu değerin altındaki (veya eşit) sonuçlar atılır.

        Returns:
            Skora göre azalan, eşitlikte ``belge_id`` artan sırada sonuçlar.
            Boş sorgu veya boş indeks için boş liste.

        Raises:
            ValueError: ``k`` negatifse.
        """
        if k < 0:
            raise ValueError("k negatif olamaz")
        if k == 0 or not self._belgeler or not isinstance(sorgu, str):
            return []

        sorgu_jetonlari = self.isleyici.jetonlar(sorgu)
        if not sorgu_jetonlari:
            return []
        sorgu_tf = Counter(sorgu_jetonlari)

        n = len(self._belgeler)
        ortalama = self._ortalama_uzunluk or 1.0
        sonuclar: list[Sonuc] = []
        for belge_id, tf in enumerate(self._terim_frekanslari):
            uzunluk = self._uzunluklar[belge_id]
            skor = 0.0
            for terim, qf in sorgu_tf.items():
                f = tf.get(terim)
                if not f:
                    continue
                idf = self._idf.get(terim, self._idf_hesapla(terim, n))
                payda = f + self.k1 * (1.0 - self.b + self.b * uzunluk / ortalama)
                skor += qf * idf * f * (self.k1 + 1.0) / payda
            if skor > min_skor:
                sonuclar.append(Sonuc(belge_id, skor, self._belgeler[belge_id]))

        sonuclar.sort(key=lambda s: (-s.skor, s.belge_id))
        return sonuclar[:k]

    # ------------------------------------------------------------------ #
    # Görünüm
    # ------------------------------------------------------------------ #
    @property
    def belge_sayisi(self) -> int:
        """İndeksteki belge sayısı."""
        return len(self._belgeler)

    @property
    def belgeler(self) -> Sequence[str]:
        """İndeksteki belgeler (salt okunur görünüm)."""
        return tuple(self._belgeler)

    @property
    def ortalama_uzunluk(self) -> float:
        """Belge başına ortalama jeton sayısı."""
        return self._ortalama_uzunluk

    @property
    def terim_sayisi(self) -> int:
        """Farklı terim sayısı."""
        return len(self._belge_frekansi)

    def __len__(self) -> int:
        return len(self._belgeler)

    def __repr__(self) -> str:
        return (
            f"BM25(belge_sayisi={self.belge_sayisi}, terim_sayisi={self.terim_sayisi}, "
            f"k1={self.k1}, b={self.b})"
        )


#: Türkçe adlandırma tercih edenler için takma ad.
BM25Indeks = BM25


def indeksle(belgeler: Iterable[str], **ayarlar: object) -> BM25:
    """Kısayol: belgelerden yeni bir :class:`BM25` indeksi kurar."""
    return BM25(belgeler, **ayarlar)  # type: ignore[arg-type]


def ara(indeks: BM25, sorgu: str, k: int = 10) -> list[Sonuc]:
    """Kısayol: hazır indekste arama yapar."""
    return indeks.search(sorgu, k=k)
