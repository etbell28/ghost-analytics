from __future__ import annotations

import csv
import json
import re
import unicodedata
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def player_key(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"\b(jr|sr|ii|iii|iv)\.?\b", "", text)
    return re.sub(r"[^a-z0-9]+", "", text)


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def schedule(date: str) -> list[dict]:
    data = get_json(f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}")
    return data.get("dates", [{}])[0].get("games", [])


def home_runs(game_pk: int, date: str) -> list[dict]:
    data = get_json(f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live")
    teams = data["gameData"]["teams"]
    game = f"{teams['away']['abbreviation']}@{teams['home']['abbreviation']}"
    events = []
    for play in data["liveData"]["plays"]["allPlays"]:
        result = play.get("result", {})
        if result.get("event") != "Home Run":
            continue
        matchup = play.get("matchup", {})
        events.append(
            {
                "date": date,
                "game": game,
                "batter": matchup.get("batter", {}).get("fullName", ""),
                "pitcher": matchup.get("pitcher", {}).get("fullName", ""),
                "inning": play.get("about", {}).get("inning"),
                "half": play.get("about", {}).get("halfInning"),
                "description": result.get("description", ""),
                "game_pk": game_pk,
            }
        )
    return events


def write_actual_results(dates: list[str]) -> list[dict]:
    results = []
    for date in dates:
        for game in schedule(date):
            results.extend(home_runs(game["gamePk"], date))

    path = ROOT / "audits" / f"hr_results_{dates[0]}_{dates[-1]}.csv".replace("-", "_")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        fields = ["date", "game", "batter", "pitcher", "inning", "half", "description", "game_pk"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    return results


def compare_sheet(date: str, actual_results: list[dict]) -> dict:
    sheet_path = ROOT / "data" / f"sheet_insights_{date.replace('-', '_')}.csv"
    if not sheet_path.exists():
        raise FileNotFoundError(f"Missing sheet snapshot: {sheet_path}")

    with sheet_path.open(newline="", encoding="utf-8", errors="ignore") as handle:
        sheet_rows = list(csv.DictReader(handle))

    actual_day = [row for row in actual_results if row["date"] == date]
    actual_keys = {player_key(row["batter"]) for row in actual_day}
    sheet_keys = {player_key(row["player"]) for row in sheet_rows}
    audit_rows = []

    for sheet in sheet_rows:
        key = player_key(sheet["player"])
        events = [row for row in actual_day if player_key(row["batter"]) == key]
        audit_rows.append(
            {
                "date": date,
                "player": sheet["player"],
                "team": sheet.get("team", ""),
                "game": sheet.get("game", ""),
                "sheet_called": "yes",
                "homered": "yes" if key in actual_keys else "no",
                "hr_count": len(events),
                "actual_pitchers": "; ".join(row["pitcher"] for row in events),
                "sheet_barrel_pct": sheet.get("sheet_barrel_pct", ""),
                "sheet_iso": sheet.get("sheet_iso", ""),
                "sheet_ev": sheet.get("sheet_ev", ""),
                "sheet_pm_hr": sheet.get("sheet_pm_hr", ""),
                "sheet_pm_pa": sheet.get("sheet_pm_pa", ""),
                "sheet_pa_pct": sheet.get("sheet_pa_pct", ""),
                "sheet_hr_env": sheet.get("sheet_hr_env", ""),
                "sheet_pitcher_split_barrel": sheet.get("sheet_pitcher_split_barrel", ""),
                "sheet_pitcher_split_hr": sheet.get("sheet_pitcher_split_hr", ""),
                "sheet_note": sheet.get("sheet_note", ""),
            }
        )

    for actual in actual_day:
        if player_key(actual["batter"]) in sheet_keys:
            continue
        audit_rows.append(
            {
                "date": date,
                "player": actual["batter"],
                "team": "",
                "game": actual["game"],
                "sheet_called": "no",
                "homered": "yes",
                "hr_count": 1,
                "actual_pitchers": actual["pitcher"],
                "sheet_note": "Unlisted official HR; add to blind-spot review",
            }
        )

    output_path = ROOT / "audits" / f"sheet_result_audit_{date.replace('-', '_')}.csv"
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        fields = sorted({key for row in audit_rows for key in row})
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(audit_rows)

    called = [row for row in audit_rows if row["sheet_called"] == "yes"]
    hits = [row for row in called if row["homered"] == "yes"]
    unlisted = [row for row in audit_rows if row["sheet_called"] == "no"]
    return {
        "date": date,
        "sheet_called_count": len(called),
        "sheet_hit_players": len(hits),
        "sheet_hit_hr_events": sum(int(row["hr_count"]) for row in hits),
        "actual_hr_events": len(actual_day),
        "unlisted_hr_events": len(unlisted),
        "hit_players": [row["player"] for row in hits],
        "unlisted_players": [row["player"] for row in unlisted],
        "audit_csv": str(output_path),
    }


def main() -> None:
    dates = ["2026-08-08", "2026-08-09"]
    actual_results = write_actual_results(dates)
    summaries = [compare_sheet(date, actual_results) for date in dates]
    summary_path = ROOT / "audits" / "sheet_result_summary_2026_08_08_09.json"
    summary_path.write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
