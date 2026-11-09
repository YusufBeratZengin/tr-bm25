"""``tokenize`` hattı: import, sıra, gövdeleme ve uçtan uca davranış."""

from __future__ import annotations

import pytest

from tr_bm25.bm25 import BM25
from tr_bm25.stem import KokBulucu, turkce_kok
from tr_bm25.tokenize import OnIsleyici, jetona_ayir


def test_tokenize_import_ve_hat_sirasi() -> None:
    """modül import edilir; durak süzme gövdelemeden önce çalışır."""
    isleyici = OnIsleyici(durak=True, kok=False, ascii_tolerans=False)
    assert isleyici.jetonlar("Kargom 12 Mart'ta gelmedi!") == [
        "kargom",
        "12",
        "mart",
        "ta",
        "gelmedi",
    ]


def test_jetona_ayir_sayilar_ve_uzunluk() -> None:
    assert jetona_ayir("Fiyatı 250 TL", sayilari_tut=False) == ["fiyatı", "tl"]
    assert jetona_ayir("a bb ccc", en_az_uzunluk=2) == ["bb", "ccc"]


def test_kok_false_govdelemez() -> None:
    isleyici = OnIsleyici(kok=False, durak=False, ascii_tolerans=False)
    assert isleyici.jetonlar("kitaplar kargom gelmedi") == [
        "kitaplar",
        "kargom",
        "gelmedi",
    ]
    assert isleyici.kok_bulucu is None


def test_kok_true_deterministik_turkce_kok() -> None:
    isleyici = OnIsleyici(kok=True, durak=False, ascii_tolerans=False)
    assert isleyici.kok_bulucu is not None
    assert isleyici.jetonlar("kitaplar kargom gelmedi") == ["kitap", "kargo", "gel"]

    # Determinizm: her çağrı ve her yeni örnek aynı sonucu verir.
    ilk = isleyici.jetonlar("kitaplar kargom gelmedi")
    assert isleyici.jetonlar("kitaplar kargom gelmedi") == ilk
    assert OnIsleyici(kok=True, durak=False).jetonlar("kitaplar kargom gelmedi")[:1] == ["kitap"]


@pytest.mark.parametrize(
    ("kelime", "beklenen"),
    [
        ("kitaplar", "kitap"),
        ("kitabı", "kitap"),
        ("kitabım", "kitap"),
        ("kitaplıktan", "kitap"),
        ("kargom", "kargo"),
        ("kargolar", "kargo"),
        ("kargoda", "kargo"),
        ("kargodan", "kargo"),
        ("kargonun", "kargo"),
        ("gelmedi", "gel"),
        ("geldi", "gel"),
        ("gelmek", "gel"),
        ("geliyor", "gel"),
        ("masasında", "masa"),
        ("ağacı", "ağaç"),
        ("evler", "ev"),
        ("şişli", "şişli"),
        ("kılıç", "kılıç"),
        ("kiliç", "kiliç"),
    ],
)
def test_turkce_kok_ornekleri(kelime: str, beklenen: str) -> None:
    assert turkce_kok(kelime) == beklenen
    assert KokBulucu().kok(kelime) == beklenen


@pytest.mark.parametrize(
    ("belge", "sorgu"),
    [
        ("defteri", "defter"),
        ("evi", "ev"),
        ("kutuyu", "kutu"),
        ("kediyi", "kedi"),
    ],
)
def test_belirtme_eki_i_kok_eslesmesi(belge: str, sorgu: str) -> None:
    """Belirtme eki ``i/yi`` gövdelemede atılmalı: sorgu belgeyi bulmalı."""
    assert turkce_kok(belge) == turkce_kok(sorgu)

    isleyici = OnIsleyici(kok=True, durak=False, ascii_tolerans=False)
    indeks = BM25(
        [belge, "alakasız metin"],
        isleyici=isleyici,
    )
    assert [s.belge_id for s in indeks.search(sorgu)] == [0]


@pytest.mark.parametrize(
    ("belge", "sorgu"),
    [
        ("bilgilerinden", "bilgi"),
        ("dergilerinden", "dergi"),
        ("vergilerinden", "vergi"),
    ],
)
def test_i_ile_biten_kokler_uc_geciste_eslesir(belge: str, sorgu: str) -> None:
    """Üç ek atılan belge ile yalın kök aynı gövdede buluşmalı."""
    isleyici = OnIsleyici(kok=True, durak=False, ascii_tolerans=False)
    indeks = BM25([belge], isleyici=isleyici)
    assert [s.belge_id for s in indeks.search(sorgu)] == [0]
    assert turkce_kok(belge) == turkce_kok(sorgu) == sorgu


@pytest.mark.parametrize("varsayilan", [False, True])
@pytest.mark.parametrize(
    ("belge", "sorgu"),
    [
        ("sergilerinden", "sergi"),
        ("sevgilerinden", "sevgi"),
        ("güvenliklerinden", "güvenlik"),
        ("bilgilerinden", "bilgi"),
        ("dergilerinden", "dergi"),
        ("vergilerinden", "vergi"),
        ("etkinliklerinden", "etkinlik"),
        ("güzelliklerinden", "güzellik"),
        ("derinliklerinden", "derinlik"),
        ("zenginliklerinden", "zenginlik"),
    ],
)
def test_cok_ekli_belge_yalin_sorguyla_eslesir(
    belge: str, sorgu: str, varsayilan: bool
) -> None:
    """Ek sayısı farklı olsa da belge ve sorgu aynı son gövdeye inmeli."""
    isleyici = (
        OnIsleyici(kok=True)
        if varsayilan
        else OnIsleyici(kok=True, durak=False, ascii_tolerans=False)
    )
    indeks = BM25([belge], isleyici=isleyici)
    assert [s.belge_id for s in indeks.search(sorgu)] == [0]
    assert turkce_kok(belge) == turkce_kok(sorgu)
    assert turkce_kok(turkce_kok(belge)) == turkce_kok(belge)


@pytest.mark.parametrize("sorgu", ["bilgi", "dergi", "vergi"])
def test_cok_ekli_eslesme_kelime_korumasina_bagli_degil(
    sorgu: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Önceki turun kelime istisnaları olmasa da eşleşme sağlanmalı."""
    from tr_bm25 import stem

    monkeypatch.setattr(stem, "_KORUNAN", stem._KORUNAN - {"bilgi", "dergi", "vergi"})
    indeks = BM25([sorgu + "lerinden"], isleyici=OnIsleyici(kok=True))
    assert [s.belge_id for s in indeks.search(sorgu)] == [0]


def test_kisa_kokler_i_ekiyle_bozulmaz() -> None:
    """Yanlış pozitif karşı testi: ``ali`` gibi kısa kökler kırpılmaz."""
    assert turkce_kok("ali") == "ali"

    isleyici = OnIsleyici(kok=True, durak=False, ascii_tolerans=False)
    indeks = BM25(["ali"], isleyici=isleyici)
    assert indeks.search("al") == []


def test_kok_bulucu_ozel_donusturucu() -> None:
    bulucu = KokBulucu(str.upper)
    assert bulucu.kok("kargo") == "KARGO"
    assert bulucu("kargo") == "KARGO"

    with pytest.raises(TypeError):
        KokBulucu("fonksiyon değil")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        bulucu.kok(42)  # type: ignore[arg-type]


def test_terim_donusturucu_kok_alaniyla_tutarli() -> None:
    """``kok`` alanı ile gerçek davranış aynı şeyi söyler."""
    temel = OnIsleyici(kok=False, durak=False, ascii_tolerans=False)
    kopya = temel.terim_donusturucu(str.upper)
    assert kopya.kok is True
    assert kopya.jetonlar("kargo") == ["KARGO"]


def test_sayilari_tut_false() -> None:
    isleyici = OnIsleyici(durak=False, sayilari_tut=False, ascii_tolerans=False)
    assert isleyici.jetonlar("kargo 12") == ["kargo"]


def test_repr_ascii_tolerans_gosterir() -> None:
    assert "ascii_tolerans=False" in repr(OnIsleyici(ascii_tolerans=False))
