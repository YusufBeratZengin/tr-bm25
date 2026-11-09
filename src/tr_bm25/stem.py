"""Türkçe gövdeleme (stemming).

Bu modül, ``tokenize`` hattının ihtiyaç duyduğu :class:`KokBulucu` API'sini
sağlar. Varsayılan gövdeleyici saf Python'dur ve dış bağımlılık gerektirmez;
böylece ``python -m pytest`` ve kurulum her ortamda aynı sonucu verir.

Tasarım ilkeleri:

* **Deterministik**: aynı jeton her zaman aynı kökü verir.
* **Tutucu**: yalnızca bilinen çekim ekleri atılır; tek harflik ekler
  yalnızca yeterince uzun gövdelere (ya da bilinen iki harfli köklere)
  uygulanır. Bu sayede ``şişli``, ``kendi`` gibi kökler yanlışlıkla
  kırpılmaz.
* **Türkçe ses olayları**: ünlüyle başlayan ek atıldığında son ünsüzün
  sertleşmesi geri alınır (``kitabı -> kitap``, ``ağacı -> ağaç``).

Daha güçlü bir gövdeleyici (ör. PyStemmer) istenirse
``KokBulucu(donusturucu)`` ile dışarıdan verilebilir; bu durumda sonuç
tamamen o dönüştürücüye bırakılır.

>>> KokBulucu().kok("kitaplar")
'kitap'
>>> KokBulucu().kok("kargom")
'kargo'
>>> KokBulucu().kok("gelmedi")
'gel'
"""

from __future__ import annotations

from collections.abc import Callable

__all__ = ["KokBulucu", "turkce_kok"]

#: Türkçe ünlüler.
_SESLI = frozenset("aeıioöuü")

#: Ünlüyle başlayan ek atıldığında geri alınacak ünsüz yumuşaması.
_SERTLESTIR = {"b": "p", "c": "ç", "d": "t", "ğ": "k", "g": "k"}

#: Tek harflik ünlü ekleri; yalnızca uzun jetonlarda ve ünsüzden sonra atılır.
_TEK_SESLI = frozenset({"ı", "i", "u", "ü"})

#: Türkçedeki yaygın iki harfli kökler. Tek harflik ünlü eki kısa jetonlarda
#: yalnızca bu köklerden sonra atılır: ``evi -> ev``, ama ``ali -> al`` değil.
_KISA_KOKLER = frozenset(
    {"ağ", "at", "ay", "el", "et", "ev", "iç", "ip", "ok", "ot", "ön", "su", "un", "ün", "üç"}
)

#: Geçmiş zaman ekleri; gövdesi ünlüyle biten sözcüklerde (ör. "kutu")
#: yanlışlıkla atılmasın diye ayrıca sınırlanır.
_GECMIS = frozenset({"dı", "di", "du", "dü", "tı", "ti", "tu", "tü"})

#: Ek gibi görünen ama kök olan sözcükler. Ek atma döngüsü bunları korur.
_KORUNAN = frozenset(
    {
        "akın", "bakın", "kadın", "kışın", "sakın", "takın", "yakın", "yazın", "şişli",
        # Önceki gövde çıktıları korunur; eşleşme bu istisnalara bağlı değildir.
        "bilgi", "dergi", "vergi",
    }
)

#: Çekim ekleri. Uzunluk sırasına göre denenir (en uzun önce).
_CEKIM_EKLERI: tuple[str, ...] = tuple(
    sorted(
        {
            # çoğul + iyelik/hâl birleşikleri
            "ları",
            "leri",
            # olumsuz + zaman
            "mıyor",
            "miyor",
            "muyor",
            "müyor",
            "medi",
            "madı",
            "memiş",
            "mamış",
            "mez",
            "maz",
            # gelecek zaman
            "acak",
            "ecek",
            "acağ",
            "eceğ",
            # şimdiki zaman
            "ıyor",
            "iyor",
            "uyor",
            "üyor",
            # görülen/duyulan geçmiş, ek fiil
            "mış",
            "miş",
            "muş",
            "müş",
            "dır",
            "dir",
            "dur",
            "dür",
            "tır",
            "tir",
            "tur",
            "tür",
            "ydı",
            "ydi",
            "ydu",
            "ydü",
            # ayrılma, tamlayan
            "dan",
            "den",
            "tan",
            "ten",
            "nun",
            "nın",
            "nin",
            "nün",
            # bulunma (iyelikle birlikte)
            "sında",
            "sinde",
            "sunda",
            "sünde",
            "ında",
            "inde",
            "unda",
            "ünde",
            # çoğul
            "lar",
            "ler",
            # mastar, sıfat-fiil, isim-fiil
            "yor",
            "ken",
            "mek",
            "mak",
            "lık",
            "lik",
            "luk",
            "lük",
            # iyelik 3. tekil, bulunma, yönelme
            "sı",
            "si",
            "su",
            "sü",
            "da",
            "de",
            "ta",
            "te",
            "ya",
            "ye",
            "yu",
            "yü",
            "yı",
            "yi",
            # tamlayan/iyelik 1. tekil
            "ın",
            "in",
            "un",
            "ün",
            "ım",
            "im",
            "um",
            "üm",
            # geçmiş zaman
            "dı",
            "di",
            "du",
            "dü",
            "tı",
            "ti",
            "tu",
            "tü",
            # tek harflik ünlü ekleri (aşağıda ayrıca sınırlanır)
            "ı",
            "i",
            "u",
            "ü",
            # iyelik 1. tekil (ünlüyle biten gövdelere)
            "m",
        },
        key=lambda ek: (-len(ek), ek),
    )
)


def _ek_at(kok: str) -> str:
    """Tek bir çekim ekini atar; uygun ek yoksa kökü aynen döndürür."""
    for ek in _CEKIM_EKLERI:
        if not kok.endswith(ek) or len(kok) <= len(ek):
            continue

        aday = kok[: -len(ek)]
        if len(aday) < 2:
            continue

        if ek in _TEK_SESLI:
            # Tek harflik ünlü eki yalnızca 5+ harflik jetonlarda ve
            # ünsüzden sonra atılır: "kitabı" -> "kitab", "defteri" ->
            # "defter", ama "kutu", "boru", "şişli" korunur. Kısa
            # jetonlarda yalnızca bilinen iki harfli kökler kırpılır
            # ("evi" -> "ev"), "ali" gibi adlar korunur.
            if aday[-1] in _SESLI:
                continue
            if len(kok) < 5 and aday not in _KISA_KOKLER:
                continue
        elif ek in {"yı", "yi"}:
            # y-kaynaştırma yalnızca ünlüyle biten gövdeye gelir:
            # "kediyi" -> "kedi", "suyu" -> "su".
            if aday[-1] not in _SESLI:
                continue
        elif ek in _GECMIS:
            # "kutu" -> "ku" olmasın; "geldi" -> "gel" korunur.
            if aday[-1] in _SESLI:
                continue
        elif ek in {"m", "n"} and len(aday) < 4:
            # "kargom" -> "kargo", ama "adam" -> "ada" olmasın.
            continue

        if ek[0] in _SESLI and aday[-1] in _SERTLESTIR:
            aday = aday[:-1] + _SERTLESTIR[aday[-1]]
        return aday

    return kok


def turkce_kok(jeton: str, *, en_fazla_gecis: int | None = None) -> str:
    """Türkçe bir jetonun çekim eklerini atarak kökünü döndürür.

    Fonksiyon saf ve deterministiktir: aynı girdi her çağrıda aynı çıktıyı
    verir. Girdinin ``turkce_kucult`` ile normalleştirilmiş olması beklenir.

    Args:
        jeton: Küçük harfli, normalleştirilmiş tek sözcük.
        en_fazla_gecis: Art arda atılabilecek en fazla ek sayısı. Varsayılan
            ``None``, ek atılamayana kadar devam eder; böylece çok ekli belge
            ile yalın sorgu aynı son gövdeye iner.

    Returns:
        Kök; hiçbir ek uymuyorsa jetonun kendisi.

    >>> turkce_kok("kitaplar")
    'kitap'
    >>> turkce_kok("kitaplıktan")
    'kitap'
    >>> turkce_kok("şişli")
    'şişli'
    """
    if not jeton or not jeton.isalpha() or len(jeton) < 3:
        return jeton

    kok = jeton
    # Her başarılı geçiş sözcüğü kısaltır; jeton uzunluğu son gövdeye
    # ulaşmak için yeterli bir üst sınırdır. Sabit üç geçiş, çok ekli
    # biçimleri sorgunun ulaşabildiği gövdeden önce durduruyordu.
    sinir = len(jeton) if en_fazla_gecis is None else max(1, en_fazla_gecis)
    for _ in range(sinir):
        if kok in _KORUNAN:
            break
        yeni = _ek_at(kok)
        if yeni == kok:
            break
        kok = yeni
    return kok


class KokBulucu:
    """Jetonları köke indirgeyen gövdeleyici.

    Args:
        donusturucu: İsteğe bağlı ``str -> str`` dönüştürücü. Verilirse
            gövdeleme tamamen ona bırakılır (ör. PyStemmer sarmalayıcısı).
            Verilmezse saf Python :func:`turkce_kok` kullanılır.

    >>> KokBulucu().kok("kitaplar")
    'kitap'
    >>> KokBulucu(str.upper).kok("kargo")
    'KARGO'
    """

    __slots__ = ("_donusturucu",)

    def __init__(self, donusturucu: Callable[[str], str] | None = None) -> None:
        if donusturucu is not None and not callable(donusturucu):
            raise TypeError("donusturucu çağrılabilir olmalı")
        self._donusturucu = donusturucu

    def kok(self, jeton: str) -> str:
        """Jetonun kökünü döndürür."""
        if not isinstance(jeton, str):
            raise TypeError(f"jeton str olmalı, {type(jeton).__name__} verildi")
        if self._donusturucu is not None:
            return self._donusturucu(jeton)
        return turkce_kok(jeton)

    #: ``kok`` için okunabilir takma ad.
    kok_al = kok

    def __call__(self, jeton: str) -> str:
        return self.kok(jeton)

    def __repr__(self) -> str:
        ad = "varsayılan" if self._donusturucu is None else repr(self._donusturucu)
        return f"KokBulucu({ad})"
