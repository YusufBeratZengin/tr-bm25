"""BM25 indeks/sorgu davranışı: IDF, sıralama ve sabit fixture."""

from __future__ import annotations

import math

import pytest

from tr_bm25 import BM25, BM25Indeks, ara, indeksle
from tr_bm25.tokenize import OnIsleyici

BELGELER = [
    "kargo bugün geldi",
    "kargo yarın gelecek",
    "kitaplar raflarda",
    "hava güzel",
]


@pytest.fixture()
def indeks() -> BM25:
    isleyici = OnIsleyici(kok=False, durak=True, ascii_tolerans=False)
    return BM25(BELGELER, isleyici=isleyici)


def test_indeks_istatistikleri(indeks: BM25) -> None:
    assert indeks.belge_sayisi == len(BELGELER)
    assert len(indeks) == len(BELGELER)
    assert indeks.ortalama_uzunluk == pytest.approx(2.5)
    assert indeks.terim_sayisi == 9


def test_idf_degerleri_fixture_uzerinde(indeks: BM25) -> None:
    # N=4, df(kargo)=2 -> ln(1 + 2.5/2.5) = ln 2
    assert indeks.idf("kargo") == pytest.approx(math.log(2.0))
    # N=4, df(kitaplar)=1 -> ln(1 + 3.5/1.5)
    assert indeks.idf("kitaplar") == pytest.approx(math.log(1.0 + 3.5 / 1.5))
    assert indeks.idf("kitaplar") > indeks.idf("kargo")
    # İndekste olmayan terim için de pozitif IDF döner.
    assert indeks.idf("yokkelime") == pytest.approx(math.log(1.0 + 4.5 / 0.5))


def test_siralama_ve_skor_formulu(indeks: BM25) -> None:
    sonuclar = indeks.search("kargo")
    assert [s.belge_id for s in sonuclar] == [0, 1]
    assert sonuclar[0].skor == pytest.approx(sonuclar[1].skor)

    # Okapi formülü: doc0 |d|=3, avgdl=2.5, tf=1
    beklenen = math.log(2.0) * (1.5 + 1.0) / (1.0 + 1.5 * (1.0 - 0.75 + 0.75 * 3 / 2.5))
    assert sonuclar[0].skor == pytest.approx(beklenen)
    assert sonuclar[0].metin == BELGELER[0]


def test_iki_terimli_sorgu_ikinci_belgeyi_one_alir(indeks: BM25) -> None:
    sonuclar = indeks.search("kargo yarın")
    assert sonuclar[0].belge_id == 1
    assert {s.belge_id for s in sonuclar} == {0, 1}
    assert sonuclar[0].skor > sonuclar[1].skor


def test_esit_skorda_belge_id_artan(indeks: BM25) -> None:
    sonuclar = indeks.search("kargo")
    assert [(s.belge_id, s.skor) for s in sonuclar] == sorted(
        [(s.belge_id, s.skor) for s in sonuclar], key=lambda x: (-x[1], x[0])
    )


def test_eslesmeyen_sorgu_bos(indeks: BM25) -> None:
    assert indeks.search("uçak") == []
    assert indeks.search("") == []
    assert indeks.search("   ") == []
    assert indeks.search("kargo", k=0) == []


def test_k_siniri(indeks: BM25) -> None:
    assert len(indeks.search("kargo", k=1)) == 1
    with pytest.raises(ValueError):
        indeks.search("kargo", k=-1)


def test_ekle_ve_yeniden_indeksleme(indeks: BM25) -> None:
    yeni_id = indeks.ekle("kargo kargo kargo")
    assert yeni_id == 4
    assert indeks.belge_sayisi == 5
    assert indeks.search("kargo")[0].belge_id == 4


def test_bos_indeks() -> None:
    bos = BM25()
    assert bos.belge_sayisi == 0
    assert bos.ortalama_uzunluk == 0.0
    assert bos.search("kargo") == []
    with pytest.raises(ValueError):
        BM25(k1=0)
    with pytest.raises(ValueError):
        BM25(b=1.5)
    with pytest.raises(TypeError):
        BM25([1, 2])  # type: ignore[list-item]


def test_arama_deterministik(indeks: BM25) -> None:
    ilk = [(s.belge_id, s.skor) for s in indeks.search("kargo")]
    for _ in range(5):
        assert [(s.belge_id, s.skor) for s in indeks.search("kargo")] == ilk


def test_turkce_adli_kisayollar() -> None:
    assert BM25Indeks is BM25
    kisa = indeksle(["kargo geldi", "kitap geldi"])
    assert [s.belge_id for s in ara(kisa, "kargo")] == [0]
