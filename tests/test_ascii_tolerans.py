"""``ascii_tolerans`` parametresi gerçekten çıktıyı değiştirmeli."""

from __future__ import annotations

from tr_bm25.normalize import ascii_katla
from tr_bm25.tokenize import OnIsleyici


def test_ascii_tolerans_farki() -> None:
    kapali = OnIsleyici(durak=False, ascii_tolerans=False)
    acik = OnIsleyici(durak=False, ascii_tolerans=True)

    assert kapali.jetonlar("Şişli kargo") == ["şişli", "kargo"]
    assert acik.jetonlar("Şişli kargo") == ["şişli", "sisli", "kargo"]
    assert kapali.jetonlar("Şişli kargo") != acik.jetonlar("Şişli kargo")


def test_ascii_tolerans_birincil_anahtari_korur() -> None:
    acik = OnIsleyici(durak=False, ascii_tolerans=True)
    jetonlar = acik.jetonlar("kılıç")
    assert jetonlar[0] == "kılıç"
    assert "kilic" in jetonlar
    # Birincil anahtar hâlâ kılıç; kiliç ile karışmıyor.
    assert "kiliç" not in jetonlar


def test_ascii_tolerans_ascii_metinde_tekrar_uretmez() -> None:
    acik = OnIsleyici(durak=False, ascii_tolerans=True)
    assert acik.jetonlar("kargo 12") == ["kargo", "12"]


def test_ascii_katla() -> None:
    assert ascii_katla("ŞİŞLİ") == "sisli"
    assert ascii_katla("geleceğ") == "geleceg"
    assert ascii_katla("kılıç") == "kilic"
