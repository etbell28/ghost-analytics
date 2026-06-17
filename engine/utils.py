from __future__ import annotations

import csv
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .config import EASTERN_TZ


def number(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, str) and not value.strip():
        return default
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(result):
        return default
    return result


def text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def confirmed(value: Any) -> bool:
    return text(value).strip().lower() in {"yes", "y", "true", "1", "confirmed"}


def eastern_now() -> datetime:
    return datetime.now(ZoneInfo(EASTERN_TZ))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8", errors="ignore") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def safe_round(value: Any, places: int = 1) -> float:
    return round(number(value), places)

