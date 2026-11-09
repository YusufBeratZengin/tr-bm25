"""Türkçe durak kelimeler ve olumsuzluk koruması.

Liste bu proje için elle derlendi (MIT). Kaynak bir kopya değildir:
Türkçe'nin işlev sözcükleri (bağlaç, edat, adıl, soru edatı, pekiştireç)
tek tek gözden geçirilerek yazıldı, bu yüzden lisans sorunu yoktur.

Standart listelerin en büyük hatası olumsuzluk sözcüklerini de silmeleri:
``değil`` ve ``yok`` atıldığında "kargo değil" ile "kargo" aynı sorguya
dönüşür. Bu modül olumsuzluğu varsayılan olarak korur; isteyen
``olumsuzluk_koru=False`` ile kapatabilir.

Durak kelime süzmesi *gövdelemeden önce*, yüzey biçimi üzerinde yapılır.
Böylece ``için`` gibi bir sözcüğün gövdesi olan ``iç`` yanlışlıkla
silinmez (``iç`` ayrı ve anlamlı bir sözcüktür).
"""

from __future__ import annotations

from collections.abc import Iterable

__all__ = [
    "OLUMSUZLUK",
    "STOPWORDS",
    "durak_mi",
    "olumsuzluk_mu",
    "suz",
]

#: Yaygın Türkçe işlev sözcükleri. Hepsi küçük harf ve normalleştirilmiş
#: biçimdedir (``â`` yerine ``a``).
STOPWORDS: frozenset[str] = frozenset(
    """
    acaba ama ancak artık aslında az
    bana bazen belki ben benden bana bize bunu bunlar bu şu
    biri birisi bir birkaç birşey biz bizden bize böyle bu buna bunu bunun
    çok çünkü
    da daha de defa değil diye dolayı dur
    eğer elbette en epey ey
    fakat falan filan
    gayet gene gibi göre
    hala hangi hangisi hani hariç hem hep her herhangi herkes hiç hiçbir
    ile için içinde ise işte
    kadar kendi kendisi kendileri ki kim kime kimse
    madem mı mi mu mü
    nasıl ne neden nedenle nerede nereye nesi neyse niçin niye
    o olan olarak olduğu olmadığı olmak olmaz olur olsa oysa
    önce öyle öbür öteki
    pek
    sadece sanki sen senden sana size siz sizden sizi sonra şayet şey şeyi
    şimdi şöyle şu şunlar şunu
    tabi tüm tümü
    üzere
    var veya ve
    yalnız yani yapacak yapılan yapmak yaptı yaptığı yaptığını yapıyor
    yine yok yoksa yukarıda yüzde
    zaten zira
    """.split()
)

#: Olumsuzluk taşıyan biçimler. ``STOPWORDS`` içinde de bulunurlar;
#: ``olumsuzluk_koru=True`` iken asla süzülmezler.
OLUMSUZLUK: frozenset[str] = frozenset(
    """
    asla değil değildi değildir değilim değiliz değiller değilmiş değilsin
    hayır hiç hiçbir
    olamaz olmadı olmadan olmayan olmaz olmayacak yok yoktu yoktur yokmuş yoksun
    """.split()
)


def durak_mi(jeton: str) -> bool:
    """Jeton durak kelime mi? (Yüzey biçimi beklenir.)"""
    return jeton in STOPWORDS


def olumsuzluk_mu(jeton: str) -> bool:
    """Jeton olumsuzluk taşıyor mu? (Yüzey biçimi beklenir.)"""
    return jeton in OLUMSUZLUK


def suz(jetonlar: Iterable[str], *, olumsuzluk_koru: bool = True) -> list[str]:
    """Durak kelimeleri süzer.

    Args:
        jetonlar: Normalize edilmiş, küçük harfli jetonlar.
        olumsuzluk_koru: ``True`` (varsayılan) iken ``OLUMSUZLUK``
            kümesindeki jetonlar, durak kelime olsalar bile korunur.

    Returns:
        Sırası korunmuş yeni bir liste.

    >>> suz(["kargo", "değil", "geldi"])
    ['kargo', 'değil', 'geldi']
    >>> suz(["kargo", "değil"], olumsuzluk_koru=False)
    ['kargo']
    """
    if olumsuzluk_koru:
        return [j for j in jetonlar if j not in STOPWORDS or j in OLUMSUZLUK]
    return [j for j in jetonlar if j not in STOPWORDS]
