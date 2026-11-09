"""``tr-bm25`` komut satırı aracı.

Örnekler::

    tr-bm25 ara "kargo nerede" belgeler/*.txt
    cat belge.txt | tr-bm25 ara "kargo"
    tr-bm25 jetonla "Kargom 12 Mart'ta gelmedi!"
    tr-bm25 --help
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .bm25 import BM25
from .tokenize import OnIsleyici

__all__ = ["main"]


def _isleyici_ayarlari(args: argparse.Namespace) -> OnIsleyici:
    return OnIsleyici(
        kok=bool(args.kok),
        durak=not bool(args.durak_yok),
        olumsuzluk_koru=not bool(args.olumsuzluk_yok),
        ascii_tolerans=not bool(args.ascii_yok),
    )


def _belgeleri_oku(dosyalar: Sequence[str]) -> tuple[list[str], list[str]]:
    """Her dosyayı bir belge olarak okur; dosya yoksa stdin tek belgedir."""
    if not dosyalar:
        return [sys.stdin.read()], ["<stdin>"]
    belgeler: list[str] = []
    adlar: list[str] = []
    for ad in dosyalar:
        yol = Path(ad)
        belgeler.append(yol.read_text(encoding="utf-8"))
        adlar.append(str(yol))
    return belgeler, adlar


def _ara(args: argparse.Namespace) -> int:
    belgeler, adlar = _belgeleri_oku(args.dosyalar)
    indeks = BM25(belgeler, isleyici=_isleyici_ayarlari(args))
    sonuclar = indeks.search(args.sorgu, k=args.adet)

    if args.json:
        print(
            json.dumps(
                [
                    {
                        "belge": adlar[s.belge_id],
                        "skor": round(s.skor, 6),
                        "metin": s.metin,
                    }
                    for s in sonuclar
                ],
                ensure_ascii=False,
            )
        )
        return 0

    if not sonuclar:
        print("Sonuç bulunamadı.", file=sys.stderr)
        return 0

    for sira, sonuc in enumerate(sonuclar, start=1):
        print(f"{sira}. {sonuc.skor:.4f}  {adlar[sonuc.belge_id]}")
    return 0


def _jetonla(args: argparse.Namespace) -> int:
    isleyici = _isleyici_ayarlari(args)
    jetonlar = isleyici.jetonlar(args.metin)
    if args.json:
        print(json.dumps(jetonlar, ensure_ascii=False))
    else:
        print("\n".join(jetonlar))
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tr-bm25",
        description="Türkçe için küçük BM25 arama aracı ve metin hattı.",
    )
    parser.add_argument(
        "--surum",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    alt = parser.add_subparsers(dest="komut", required=True, metavar="{ara,jetonla}")

    ara = alt.add_parser("ara", help="Belgelerde BM25 araması yapar")
    ara.add_argument("sorgu", help="Arama sorgusu")
    ara.add_argument(
        "dosyalar",
        nargs="*",
        help="UTF-8 metin dosyaları (her dosya bir belge). Verilmezse stdin okunur.",
    )
    ara.add_argument("-k", "--adet", type=int, default=10, help="Sonuç sayısı (varsayılan 10)")
    ara.add_argument("--kok", action="store_true", help="Gövdelemeyi aç")
    ara.add_argument("--durak-yok", action="store_true", help="Durak kelime süzmesini kapat")
    ara.add_argument(
        "--olumsuzluk-yok",
        action="store_true",
        help="Olumsuzluk korumasını kapat (değil/yok da süzülür)",
    )
    ara.add_argument("--ascii-yok", action="store_true", help="ASCII tolerans anahtarlarını kapat")
    ara.add_argument("--json", action="store_true", help="JSON çıktısı üret")
    ara.set_defaults(func=_ara)

    jetonla = alt.add_parser("jetonla", help="Metni indeks terimlerine ayırır")
    jetonla.add_argument("metin", help="Jetonlara ayrılacak metin")
    jetonla.add_argument("--kok", action="store_true", help="Gövdelemeyi aç")
    jetonla.add_argument("--durak-yok", action="store_true", help="Durak kelime süzmesini kapat")
    jetonla.add_argument(
        "--olumsuzluk-yok",
        action="store_true",
        help="Olumsuzluk korumasını kapat",
    )
    jetonla.add_argument(
        "--ascii-yok", action="store_true", help="ASCII tolerans anahtarlarını kapat"
    )
    jetonla.add_argument("--json", action="store_true", help="JSON çıktısı üret")
    jetonla.set_defaults(func=_jetonla)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI giriş noktası. Dönüş değeri süreç çıkış kodudur."""
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (OSError, UnicodeDecodeError) as hata:
        print(f"tr-bm25: {hata}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
