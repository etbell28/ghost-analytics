from __future__ import annotations

import argparse
from pathlib import Path

from .payload import build_from_rankings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to a rankings CSV")
    parser.add_argument("--output", required=True, help="Path to write Ghost live JSON")
    args = parser.parse_args()
    payload = build_from_rankings(Path(args.input), Path(args.output))
    print(f"Wrote {args.output}")
    print(f"Players: {payload['status']['total_players']}")
    print(f"Pairings 2/3/4: {len(payload['pairings']['2'])}/{len(payload['pairings']['3'])}/{len(payload['pairings']['4'])}")


if __name__ == "__main__":
    main()

