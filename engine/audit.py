from __future__ import annotations

import json
from pathlib import Path

from .utils import eastern_now


def create_audit_stub(live_payload_path: Path, output_path: Path) -> dict:
    payload = json.loads(live_payload_path.read_text(encoding="utf-8"))
    now = eastern_now()
    report = {
        "report_date": now.date().isoformat(),
        "generated_at": now.isoformat(),
        "product": payload.get("product", "BarrelIQ"),
        "input_payload": str(live_payload_path),
        "status": "framework_ready",
        "summary": {
            "top_targets": len(payload.get("top_targets", [])),
            "confirmed_targets": len(payload.get("confirmed_targets", [])),
            "projected_targets": len(payload.get("projected_targets", [])),
            "pairings_2": len(payload.get("pairings", {}).get("2", [])),
            "pairings_3": len(payload.get("pairings", {}).get("3", [])),
            "pairings_4": len(payload.get("pairings", {}).get("4", [])),
        },
        "next_required_input": "official MLB result feed / boxscore HR events",
        "miss_categories": [
            "Player not in pool",
            "Ranked too low",
            "Weather underweighted",
            "Pitcher split missed",
            "Lineup changed",
            "Hot bat overvalued",
            "Pairing concentration error",
            "Data source failed",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report

