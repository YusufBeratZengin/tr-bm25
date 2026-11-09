"""Jeton ayırma ve ön işleme hattı.

Hat sırası önemlidir::

    metin -> temizle -> Türkçe küçült -> düzeltme işareti katla
          -> jetonla -> (durak süz) -> (gövdele) -> terim

Durak süzme gövdelemeden *önce* yapılır; gövdeleme sonrası yapılsaydı
``için`` sözcüğünün gövdesi olan ``iç`` de silinirdi.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from .normalize import ascii_katla, normalestir
from .stem import KokBulucu
from .stopwords import suz

__all__ = ["JETON_DESENI", "OnIsleyici", "jetona_ayir"]

#: Harf ve rakamlardan oluşan jetonlar. Alt çizgi jeton sayılmaz;
#: kesme işareti, noktalama ve boşluk ayırıcıdır.
JETON_DESENI = re.compile(r"[^\W_]+", re.UNICODE)


def jetona_ayir(metin: str, *, sayilari_tut: bool = True, en_az_uzunluk: int = 1) -> list[str]:
    """Metni jetonlara ayırır, arama için normalleştirir.

    >>> jetona_ayir("Kargom 12 Mart'ta gelmedi!")
    ['kargom', '12', 'mart', 'ta', 'gelmedi']
    >>> jetona_ayir("Fiyatı 250 TL", sayilari_tut=False)
    ['fiyatı', 'tl']
    """
    normal = normalestir(metin)
    jetonlar = JETON_DESENI.findall(normal)
    if not sayilari_tut:
        jetonlar = [j for j in jetonlar if not j.isdigit()]
    if en_az_uzunluk > 1:
        jetonlar = [j for j in jetonlar if len(j) >= en_az_uzunluk]
    return jetonlar


class OnIsleyici:
    """Belge ve sorgu metinlerini aynı biçime getiren hat.

    Args:
        kok: Gövdeleme açık mı? ``True`` ise her jeton :class:`~.stem.KokBulucu`
            üzerinden köke indirgenir. Dış bağımlılık gerekmez.
        durak: Durak kelime süzmesi açık mı?
        olumsuzluk_koru: ``değil``/``yok`` gibi sözcükler korunsun mu?
        ascii_tolerans: ``True`` iken her Türkçe harfli terim için hemen
            ardından ASCII katlanmış ikincil anahtar da üretilir (ör.
            ``şişli -> ["şişli", "sisli"]``). Birincil anahtar korunur;
            bu anahtar Türkçe klavyesi olmayan sorguların eşleşmesini
            sağlar. ``False`` iken yalnızca birincil terimler döner.
        kok_bulucu: Test veya özel amaçla dışarıdan verilebilen gövdeleyici.
            Verilmesi gövdelemeyi açar (``kok=True`` ile aynı etki).
        sayilari_tut: Saf sayı jetonları tutulsun mu?
    """

    def __init__(
        self,
        *,
        kok: bool = False,
        durak: bool = True,
        olumsuzluk_koru: bool = True,
        ascii_tolerans: bool = True,
        kok_bulucu: KokBulucu | None = None,
        sayilari_tut: bool = True,
    ) -> None:
        self.kok = kok or kok_bulucu is not None
        self.durak = durak
        self.olumsuzluk_koru = olumsuzluk_koru
        self.ascii_tolerans = ascii_tolerans
        self.sayilari_tut = sayilari_tut
        if kok_bulucu is not None:
            self._kok_bulucu: KokBulucu | None = kok_bulucu
        elif kok:
            self._kok_bulucu = KokBulucu()
        else:
            self._kok_bulucu = None

    @property
    def kok_bulucu(self) -> KokBulucu | None:
        return self._kok_bulucu

    def ham_jetonlar(self, metin: str) -> list[str]:
        """Normalleştirilmiş, süzülmemiş jetonlar (hata ayıklama için)."""
        return jetona_ayir(metin, sayilari_tut=self.sayilari_tut)

    def jetonlar(self, metin: str) -> list[str]:
        """Metni indeks terimlerine çevirir (gövdeleme dâhil).

        ``ascii_tolerans`` açıksa, birincil terimin hemen ardından ASCII
        katlanmış ikincil anahtar da eklenir; anahtar birincil terimle
        aynıysa tekrar edilmez.
        """
        jetonlar = self.ham_jetonlar(metin)
        if self.durak:
            jetonlar = suz(jetonlar, olumsuzluk_koru=self.olumsuzluk_koru)
        if self.kok and self._kok_bulucu is not None:
            jetonlar = [self._kok_bulucu.kok(j) for j in jetonlar]
        if self.ascii_tolerans:
            jetonlar = self._ascii_anahtarlari_ekle(jetonlar)
        return jetonlar

    @staticmethod
    def _ascii_anahtarlari_ekle(jetonlar: list[str]) -> list[str]:
        """Her terimin ardından farklıysa ASCII katlanmış anahtarını ekler."""
        sonuc: list[str] = []
        for jeton in jetonlar:
            sonuc.append(jeton)
            ascii_jeton = ascii_katla(jeton)
            if ascii_jeton != jeton:
                sonuc.append(ascii_jeton)
        return sonuc

    def terim_donusturucu(self, donusturucu: Callable[[str], str]) -> OnIsleyici:
        """Aynı ayarlarla, verilen gövdeleyiciyi kullanan kopya üretir.

        Dönüştürücü verildiği için kopyada ``kok`` alanı ``True`` olur;
        böylece alan ile gerçek davranış birbiriyle tutarlı kalır.
        """
        return OnIsleyici(
            kok=True,
            durak=self.durak,
            olumsuzluk_koru=self.olumsuzluk_koru,
            ascii_tolerans=self.ascii_tolerans,
            kok_bulucu=KokBulucu(donusturucu),
            sayilari_tut=self.sayilari_tut,
        )

    def __repr__(self) -> str:
        return (
            f"OnIsleyici(kok={self.kok}, durak={self.durak}, "
            f"olumsuzluk_koru={self.olumsuzluk_koru}, ascii_tolerans={self.ascii_tolerans})"
        )
