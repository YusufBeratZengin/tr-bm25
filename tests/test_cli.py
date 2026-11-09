"""CLI: ``tr-bm25`` alt komutları ve ``--help``."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tr_bm25.cli import main

PROJE_KOKU = Path(__file__).resolve().parents[1]


def _yaz(yol: Path, metin: str) -> Path:
    yol.write_text(metin, encoding="utf-8")
    return yol


def test_cli_arama(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    kargo = _yaz(tmp_path / "kargo.txt", "kargo bugün geldi")
    kitap = _yaz(tmp_path / "kitap.txt", "kitaplar raflarda")
    assert main(["ara", "kargo", str(kargo), str(kitap)]) == 0
    cikti = capsys.readouterr().out
    satirlar = cikti.strip().splitlines()
    assert satirlar[0].startswith("1.")
    assert str(kargo) in satirlar[0]
    assert str(kitap) not in cikti


def test_cli_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    belge = _yaz(tmp_path / "a.txt", "kargo geldi")
    assert main(["ara", "--json", "kargo", str(belge)]) == 0
    veri = json.loads(capsys.readouterr().out)
    assert veri[0]["belge"] == str(belge)
    assert veri[0]["skor"] > 0
    assert veri[0]["metin"] == "kargo geldi"


def test_cli_jetonla(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["jetonla", "Kitaplar raflarda", "--kok", "--ascii-yok"]) == 0
    assert capsys.readouterr().out.split() == ["kitap", "raf"]


def test_cli_jetonla_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["jetonla", "Şişli", "--durak-yok", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == ["şişli", "sisli"]


def test_cli_dosya_yok(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["ara", "kargo", str(tmp_path / "yok.txt")]) == 1
    assert "tr-bm25:" in capsys.readouterr().err


def test_cli_help_alt_surec() -> None:
    """``tr-bm25 --help`` exit 0 dönmeli."""
    env = {**os.environ, "PYTHONPATH": str(PROJE_KOKU / "src")}
    sonuc = subprocess.run(
        [sys.executable, "-m", "tr_bm25.cli", "--help"],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    assert sonuc.returncode == 0
    assert "ara" in sonuc.stdout
    assert "jetonla" in sonuc.stdout

    surum = subprocess.run(
        [sys.executable, "-m", "tr_bm25.cli", "--surum"],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )
    assert surum.returncode == 0
    assert "0.1.0" in surum.stdout
