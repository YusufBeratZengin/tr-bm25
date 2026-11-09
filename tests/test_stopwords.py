"""Durak kelime süzme ve olumsuzluk koruması — hem ``suz`` hem uçtan uca."""

from __future__ import annotations

import pytest

from tr_bm25.stopwords import OLUMSUZLUK, STOPWORDS, durak_mi, olumsuzluk_mu, suz
from tr_bm25.tokenize import OnIsleyici


def test_suz_negasyon_korunur() -> None:
    assert suz(["kargo", "değil", "geldi"]) == ["kargo", "değil", "geldi"]
    assert suz(["kargo", "değil"], olumsuzluk_koru=False) == ["kargo"]


@pytest.mark.parametrize("jeton", ["değil", "yok", "hiç", "hiçbir"])
def test_olumsuzluk_kumesi_durak_kelime_ama_korunur(jeton: str) -> None:
    assert durak_mi(jeton)
    assert olumsuzluk_mu(jeton)
    assert jeton in STOPWORDS
    assert jeton in OLUMSUZLUK
    assert suz([jeton, "kargo"]) == [jeton, "kargo"]


def test_olumsuzluk_durak_kelime_olmayabilir() -> None:
    """``asla`` olumsuzluk taşır ama zaten durak kelime değildir."""
    assert olumsuzluk_mu("asla")
    assert not durak_mi("asla")
    assert suz(["asla", "kargo"]) == ["asla", "kargo"]


def test_negasyon_ucdan_uca_on_isleyici() -> None:
    koruyan = OnIsleyici(durak=True, olumsuzluk_koru=True, ascii_tolerans=False)
    silen = OnIsleyici(durak=True, olumsuzluk_koru=False, ascii_tolerans=False)

    assert koruyan.jetonlar("kargo değil") == ["kargo", "değil"]
    assert silen.jetonlar("kargo değil") == ["kargo"]
    assert koruyan.jetonlar("kargo yok") == ["kargo", "yok"]
    assert silen.jetonlar("kargo yok") == ["kargo"]


def test_durak_suzme_sirasi_govdelemeden_once() -> None:
    """``için`` süzülürken anlamlı ``iç`` gövdesi korunur."""
    isleyici = OnIsleyici(kok=True, durak=True, ascii_tolerans=False)
    assert isleyici.jetonlar("iç için kargo") == ["iç", "kargo"]


def test_suz_sira_korunur_ve_yeni_liste() -> None:
    girdi = ["için", "kargo", "bir", "geldi"]
    cikti = suz(girdi)
    assert cikti == ["kargo", "geldi"]
    assert cikti is not girdi
    assert girdi == ["için", "kargo", "bir", "geldi"]
