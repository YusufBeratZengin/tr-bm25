"""Paketleme regresyonu: wheel kurulabilir, sürüm ve CLI giriş noktası var.

Build izolasyonu kullanılır; hatchling
zaten kuruluysa ağ erişimi gerekmez.
"""

from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

PROJE_KOKU = Path(__file__).resolve().parents[1]

#: ``license-files`` (PEP 639) desteği için gereken en düşük hatchling sürümü.
EN_AZ_HATCHLING = (1, 27)


def _hatchling_gereksinimi(gereksinimler: list[str]) -> str | None:
    for gereksinim in gereksinimler:
        ad = re.split(r"[\s<>=!~;\[(]", gereksinim, maxsplit=1)[0].strip().lower()
        if ad == "hatchling":
            return gereksinim
    return None


def _alt_sinir(gereksinim: str) -> tuple[int, ...] | None:
    eslesme = re.search(r">=\s*([0-9]+(?:\.[0-9]+)*)", gereksinim)
    if eslesme is None:
        return None
    return tuple(int(parca) for parca in eslesme.group(1).split("."))


def test_hatchling_alt_siniri_yeterli() -> None:
    """``license-files`` için hatchling alt sınırı >= 1.27 olmalı."""
    tomllib = pytest.importorskip("tomllib")  # stdlib from Python 3.11
    veri = tomllib.loads((PROJE_KOKU / "pyproject.toml").read_text(encoding="utf-8"))
    gereksinimler = veri["build-system"]["requires"]
    gereksinim = _hatchling_gereksinimi(gereksinimler)
    assert gereksinim is not None, f"hatchling build gereksinimi yok: {gereksinimler}"

    alt_sinir = _alt_sinir(gereksinim)
    assert alt_sinir is not None, f"hatchling alt sınırı belirtilmemiş: {gereksinim!r}"

    # (1, 27) ile (1, 27, 0) eşdeğer sayılsın.
    doldurulmus = alt_sinir + (0,) * (len(EN_AZ_HATCHLING) - len(alt_sinir))
    assert doldurulmus >= EN_AZ_HATCHLING, (
        f"hatchling alt sınırı {alt_sinir} < {EN_AZ_HATCHLING}; "
        "license-files PEP 639 desteği için >=1.27 gerekir"
    )


def _calistir(komut: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        komut,
        capture_output=True,
        text=True,
        timeout=600,
        **kwargs,  # type: ignore[arg-type]
    )


@pytest.fixture(scope="module")
def tekerlek(tmp_path_factory: pytest.TempPathFactory) -> Path:
    if importlib.util.find_spec("pip") is None:
        pytest.skip("pip yok; wheel testi atlandı")

    hedef = tmp_path_factory.mktemp("tekerlek")
    komut = [
        sys.executable,
        "-m",
        "pip",
        "wheel",
        "--no-cache-dir",
        "--no-deps",
    ]
    if importlib.util.find_spec("hatchling") is not None:
        komut.append("--no-build-isolation")
    komut.extend([str(PROJE_KOKU), "-w", str(hedef)])

    sonuc = _calistir(komut, cwd=str(PROJE_KOKU))
    if sonuc.returncode != 0:
        pytest.fail(f"wheel derlenemedi:\nSTDOUT:\n{sonuc.stdout}\nSTDERR:\n{sonuc.stderr}")

    dosyalar = sorted(hedef.glob("tr_bm25-*.whl"))
    assert len(dosyalar) == 1, dosyalar
    return dosyalar[0]


def test_tekerlek_icerigi(tekerlek: Path) -> None:
    with zipfile.ZipFile(tekerlek) as arsiv:
        adlar = set(arsiv.namelist())
        assert "tr_bm25/__init__.py" in adlar
        assert "tr_bm25/stem.py" in adlar
        assert "tr_bm25/cli.py" in adlar
        assert "tr_bm25/bm25.py" in adlar

        giris_noktalari = [ad for ad in adlar if ad.endswith("entry_points.txt")]
        assert giris_noktalari, "entry_points.txt wheel içinde yok"
        icerik = arsiv.read(giris_noktalari[0]).decode("utf-8")
        assert "tr-bm25 = tr_bm25.cli:main" in icerik


def test_kurulu_paket_surum_ve_cli(
    tekerlek: Path, tmp_path: Path
) -> None:
    site = tmp_path / "site"
    kurulum = _calistir(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-cache-dir",
            "--no-deps",
            "--target",
            str(site),
            str(tekerlek),
        ]
    )
    assert kurulum.returncode == 0, kurulum.stderr

    env = {**os.environ, "PYTHONPATH": str(site), "PYTHONNOUSERSITE": "1"}

    surum = _calistir(
        [
            sys.executable,
            "-c",
            "import tr_bm25, importlib.metadata as m; "
            "print(tr_bm25.__version__, m.version('tr-bm25'))",
        ],
        cwd=str(tmp_path),
        env=env,
    )
    assert surum.returncode == 0, surum.stderr
    assert surum.stdout.split() == ["0.1.0", "0.1.0"]

    # With --target pip uses "bin"; the launcher is "tr-bm25.exe" on Windows.
    adaylar = sorted(site.glob("bin/tr-bm25*")) + sorted(site.glob("Scripts/tr-bm25*"))
    if not adaylar:
        pytest.fail(f"konsol betiği üretilmemiş: {site}")
    betik = adaylar[0]

    yardim = _calistir([str(betik), "--help"], cwd=str(tmp_path), env=env)
    assert yardim.returncode == 0, yardim.stderr
    assert "ara" in yardim.stdout
    assert "jetonla" in yardim.stdout
