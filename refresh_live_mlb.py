from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from engine.audit import create_audit_stub
from engine.payload import build_from_rankings


ROOT = Path(__file__).parent
OUTPUTS = ROOT / "outputs"
EASTERN = ZoneInfo("America/New_York")


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def choose_mode(requested: str) -> str:
    if requested in {"full", "remaining"}:
        return requested
    now = datetime.now(EASTERN)
    # Before most lineups settle, build all upcoming games. Once games are active,
    # use upcoming/remaining games only.
    if now.hour < 16:
        return "full"
    return "remaining"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["auto", "full", "remaining"], default="auto")
    args = parser.parse_args()
    mode = choose_mode(args.mode)

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    slate_path = OUTPUTS / ("auto_slate_full.csv" if mode == "full" else "auto_slate_remaining.csv")
    slate_mode = "all" if mode == "full" else "upcoming"

    run([sys.executable, "build_automated_slate.py", "--mode", slate_mode, "--output", str(slate_path)])
    run([sys.executable, "hitter_tool.py", str(slate_path)])

    payload_path = OUTPUTS / "live_mlb_payload.json"
    build_from_rankings(OUTPUTS / "hr_rankings.csv", payload_path)
    create_audit_stub(payload_path, ROOT / "audits" / "latest_audit_stub.json")

    print(f"GhostIQ MLB refresh complete: {mode}")
    print(f"Payload: {payload_path}")


if __name__ == "__main__":
    main()

