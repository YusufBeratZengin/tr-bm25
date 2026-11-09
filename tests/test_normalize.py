"""Türkçe normalleştirme ve görünmez karakter regresyonları."""

from __future__ import annotations

import unicodedata

import pytest

from tr_bm25.normalize import (
    BIRLESIK_NOKTA,
    ascii_katla,
    normalestir,
    temizle,
    turkce_kucult,
)
from tr_bm25.tokenize import jetona_ayir


@pytest.mark.parametrize(
    ("girdi", "beklenen"),
    [
        ("İ", "i"),
        ("I", "ı"),
        ("I" + BIRLESIK_NOKTA, "i"),  # ayrıştırılmış İ
        ("İSTANBUL", "istanbul"),
        ("ISPARTA", "ısparta"),
        ("I" + BIRLESIK_NOKTA + "ZMİR", "izmir"),
        ("Kılıç", "kılıç"),
    ],
)
def test_turkce_kucult_cekirdek(girdi: str, beklenen: str) -> None:
    assert turkce_kucult(girdi) == beklenen


def test_ayristirilmis_girdi_nfc_ile_birlesir() -> None:
    ayrik = "I" + BIRLESIK_NOKTA
    assert unicodedata.normalize("NFC", ayrik) == "İ"
    assert turkce_kucult(ayrik) == turkce_kucult("İ") == "i"


def test_kucultme_idempotan() -> None:
    for metin in ["İSTANBUL", "IŞIK", "Kılıç", "I" + BIRLESIK_NOKTA + "ZMİR", "ğÜŞiÖÇ"]:
        bir = turkce_kucult(metin)
        assert turkce_kucult(bir) == bir
        assert unicodedata.is_normalized("NFC", bir)


def test_kilic_ile_kilic_ayrimi_korunur() -> None:
    """Birincil anahtarda ı ≠ i; yalnızca ASCII toleransı birleştirir."""
    assert normalestir("Kılıç") == "kılıç"
    assert normalestir("Kiliç") == "kiliç"
    assert normalestir("Kılıç") != normalestir("Kiliç")
    assert ascii_katla("Kılıç") == ascii_katla("Kiliç") == "kilic"


def test_normalestir_ince_isaret() -> None:
    assert normalestir("HÂLÂ") == "hala"
    assert normalestir("HÂLÂ", ince_isaret=False) == "hâlâ"


def test_normalestir_all_icinde() -> None:
    """yıldızlı import normalestir'i kaybetmemeli."""
    ad_alanı: dict[str, object] = {}
    exec("from tr_bm25.normalize import *", ad_alanı)
    assert "normalestir" in ad_alanı
    assert callable(ad_alanı["normalestir"])


@pytest.mark.parametrize(
    ("girdi", "beklenen"),
    [
        ("ke\u00adlim", ["kelim"]),  # soft hyphen
        ("kitap\u2060lar", ["kitaplar"]),  # word joiner
        ("\ufeffkargo", ["kargo"]),  # BOM
        ("\u200b", []),  # zero-width space
        ("kar\u200bgo", ["kargo"]),  # kelime ortasında ZWSP
        ("\u180ekargo", ["kargo"]),  # Moğol ünlü ayırıcı
        ("\u061ckargo", ["kargo"]),  # Arapça harf işareti
    ],
)
def test_temizle_gorunmez_karakterler(girdi: str, beklenen: list[str]) -> None:
    assert jetona_ayir(girdi) == beklenen


def test_temizle_girdiyi_degistirmez() -> None:
    metin = "ke\u00adlim"
    assert temizle(metin) == "kelim"
    assert metin == "ke\u00adlim"


def test_temizle_tip_hatasi_mesaji() -> None:
    with pytest.raises(TypeError, match="int"):
        temizle(42)  # type: ignore[arg-type]
