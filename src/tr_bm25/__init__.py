"""tr-bm25 — Türkçe için küçük, bağımlılıksız BM25 arama.

Paket kökü, sürümü ve genel API'yi dışa açar::

    >>> import tr_bm25
    >>> tr_bm25.__version__
    '0.1.0'
    >>> indeks = tr_bm25.BM25(["kargo bugün geldi", "kitaplar raflarda"])
    >>> [s.belge_id for s in indeks.search("kargo")]
    [0]

Türkçe'ye özgü davranışlar:

* ``İ -> i``, ``I -> ı`` (``str.lower()`` yanlış sonuç verir),
* ``kılıç`` ile ``kiliç`` birincil anahtarda ayrı kalır,
* ``değil``/``yok`` gibi olumsuzluk sözcükleri durak süzmede korunur,
* soft hyphen, BOM, word joiner gibi görünmez karakterler temizlenir.
"""

from __future__ import annotations

from .bm25 import BM25, BM25Indeks, Sonuc, ara, indeksle
from .normalize import (
    ascii_katla,
    bosluk_sikistir,
    katla,
    normalestir,
    temizle,
    turkce_kucult,
)
from .stem import KokBulucu, turkce_kok
from .stopwords import OLUMSUZLUK, STOPWORDS, suz
from .tokenize import JETON_DESENI, OnIsleyici, jetona_ayir

__version__ = "0.1.0"
__all__ = [
    "BM25",
    "BM25Indeks",
    "JETON_DESENI",
    "KokBulucu",
    "OLUMSUZLUK",
    "OnIsleyici",
    "STOPWORDS",
    "Sonuc",
    "__version__",
    "ara",
    "ascii_katla",
    "bosluk_sikistir",
    "indeksle",
    "jetona_ayir",
    "katla",
    "normalestir",
    "suz",
    "temizle",
    "turkce_kok",
    "turkce_kucult",
]
