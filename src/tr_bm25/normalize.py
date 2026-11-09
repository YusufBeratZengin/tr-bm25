"""Türkçe metin normalleştirme.

Bu modülün tek işi metni arama için karşılaştırılabilir hâle getirmek.
Türkçe'de iki büyük tuzak vardır:

1. ``str.lower()`` Türkçe için yanlıştır. ``"İ".lower()`` Python'da
   ``"i" + U+0307`` (i + birleşik nokta) üretir, ``"I".lower()`` ise
   ``"i"`` verir; doğrusu sırasıyla ``"i"`` ve ``"ı"``.
2. ``ı`` ile ``i`` ayrı harflerdir. Bunları birleştirmek aramayı bozar
   (``kılıç`` ≠ ``kiliç``). ASCII'ye indirgeme yalnızca *ayrı* bir
   tolerans katmanında, isteğe bağlı olarak yapılır.

ASCII'ye indirgeme (``ascii_katla``) kullanıcı Türkçe karakterleri
yazamadığında devreye girer: ``geleceğ`` ↔ ``geleceg``, ``kılıç`` ↔
``kilic``. Bu katman birincil anahtarı asla değiştirmez; yalnızca isteğe
bağlı bir tolerans anahtarı üretir. Tolerans katmanında ``ı`` ile ``i``
bilinçli olarak birleşir.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "BIRLESIK_NOKTA",
    "ascii_katla",
    "bosluk_sikistir",
    "katla",
    "normalestir",
    "turkce_kucult",
    "temizle",
]

#: ``"İ".lower()`` sonucunda ortaya çıkan birleşik nokta.
BIRLESIK_NOKTA = "\u0307"

#: Türkçe yazıda kullanılan düzeltme işaretli harfler (â, î, û, ô).
_INCE_ISARETLI = {"â": "a", "î": "i", "û": "u", "ô": "o"}

#: ASCII katlamada kullanılan harf eşlemesi. ``ı -> i`` burada bilinçli:
#: tolerans katmanının amacı Türkçe karakteri olmayan klavyeyi affetmek.
_ASCII_ESLEME = str.maketrans(
    {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
        "â": "a",
        "î": "i",
        "û": "u",
        "ô": "o",
    }
)

_KONTROL = re.compile(
    r"[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f"
    r"\u00ad\u061c\u180e\u200b-\u200f\u2028\u2029\u2060\ufeff]"
)


def temizle(metin: str) -> str:
    """Görünmez denetim karakterlerini ve sıfır genişlikli işaretleri atar.

    Soft hyphen (``U+00AD``), word joiner (``U+2060``), Moğol ünlü ayırıcı
    (``U+180E``), Arapça harf işareti (``U+061C``) ve BOM (``U+FEFF``) dâhil
    olmak üzere PDF/kopyala-yapıştır metinlerinde görülen görünmez
    karakterler silinir. Girdi metni değiştirilmez; yeni bir ``str`` döner.

    >>> temizle("ke\\u00adlim")
    'kelim'
    >>> temizle("kitap\\u2060lar")
    'kitaplar'
    """
    if not isinstance(metin, str):
        raise TypeError(f"metin str olmalı, {type(metin).__name__} verildi")
    return _KONTROL.sub("", metin)


def turkce_kucult(metin: str) -> str:
    """Türkçe kurallarına uygun küçük harfe çevirir.

    ``İ -> i`` ve ``I -> ı`` eşlemesi ``str.lower()`` çağrısından *önce*
    yapılır; böylece birleşik nokta hiç oluşmaz. Yine de başka
    kaynaklardan gelen ``U+0307`` temizlenir.

    >>> turkce_kucult("İSTANBUL")
    'istanbul'
    >>> turkce_kucult("ISPARTA")
    'ısparta'
    >>> turkce_kucult("Kılıç")
    'kılıç'
    """
    metin = unicodedata.normalize("NFC", temizle(metin))
    metin = metin.replace("\u0130", "i").replace("I", "\u0131")
    return metin.lower().replace(BIRLESIK_NOKTA, "")


def katla(metin: str) -> str:
    """Düzeltme işaretlerini sadeleştirir (``â -> a``, ``î -> i``, ``û -> u``).

    Arama için ``hâlâ`` ile ``hala`` aynı kefeye gelir; yazım denetimi
    yapılmaz, yalnızca eşleşme kolaylaşır. Girdi küçük harfe çevrilmiş
    olmalıdır (``turkce_kucult`` çıktısı).
    """
    for kaynak, hedef in _INCE_ISARETLI.items():
        metin = metin.replace(kaynak, hedef)
    return metin


def ascii_katla(metin: str) -> str:
    """Türkçe harfleri ASCII karşılıklarına indirger.

    Bu fonksiyon *yalnızca* tolerans katmanında kullanılır. Birincil
    indeks anahtarı olarak kullanılmamalıdır; ``ı`` ile ``i`` ayrımı
    burada bilinçli olarak kaybolur.

    >>> ascii_katla("geleceğe")
    'gelecege'
    >>> ascii_katla("ŞİŞLİ")
    'sisli'
    """
    return turkce_kucult(metin).translate(_ASCII_ESLEME)


def bosluk_sikistir(metin: str) -> str:
    """Ardışık boşlukları tek boşluğa indirger ve uçları kırpar."""
    return " ".join(metin.split())


def normalestir(metin: str, *, ince_isaret: bool = True) -> str:
    """Kısayol: temizle + Türkçe küçült + (isteğe bağlı) düzeltme işareti katla."""
    sonuc = turkce_kucult(metin)
    if ince_isaret:
        sonuc = katla(sonuc)
    return bosluk_sikistir(sonuc)
