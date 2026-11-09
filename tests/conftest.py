"""Testlerin kaynak ağacını görmesini garanti eder.

``pyproject.toml`` içindeki ``pythonpath = ["src"]`` yeterlidir; bu dosya
ayarın okunmadığı özel çağrılarda (ör. ``pytest --no-config``) da testlerin
çalışmasını sağlar.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJE_KOKU = Path(__file__).resolve().parents[1]
SRC = PROJE_KOKU / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
