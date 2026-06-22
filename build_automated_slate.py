import argparse
import csv
import html
import json
import re
import unicodedata
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path


ROOT = Path(__file__).parent
OUTPUT_PATH = ROOT / "outputs" / "auto_slate_late.csv"
DAILY_DIR = ROOT / "outputs" / "daily"
ROTOWIRE_LINEUPS_URL = "https://www.rotowire.com/baseball/daily-lineups.php"
HISTORY_WEIGHTS = {
    0: 0.70,
    -1: 0.30,
}


BATTER_URL = (
    "https://baseballsavant.mlb.com/leaderboard/custom?"
    "year={year}&type=batter&filter=&min=1&"
    "selections=pa%2Cxslg%2Cxwoba%2Cxiso%2Cexit_velocity_avg%2C"
    "avg_best_speed%2Cavg_hyper_speed%2Cavg_swing_speed%2C"
    "fast_swing_rate%2Cbarrel_batted_rate%2Chard_hit_percent%2C"
    "pull_percent%2Cflyballs_percent%2Cisolated_power%2Chome_run&chart=false&x=pa&y=pa&"
    "r=no&chartType=beeswarm&sort=xwoba&sortDir=desc&csv=true"
)


PITCHER_URL = (
    "https://baseballsavant.mlb.com/leaderboard/custom?"
    "year={year}&type=pitcher&filter=&min=1&"
    "selections=pa%2Ck_percent%2Cbb_percent%2Cbatting_avg%2Cslg_percent%2C"
    "on_base_plus_slg%2Cisolated_power%2Cp_era%2Cxslg%2Cxwoba%2Cxiso%2C"
    "exit_velocity_avg%2Cbarrel%2Cbarrel_batted_rate%2Chard_hit_percent%2C"
    "whiff_percent%2Cpull_percent%2Cbatted_ball%2Cgroundballs_percent%2C"
    "flyballs_percent%2Clinedrives_percent%2Cpopups_percent%2Chome_run&"
    "chart=false&x=pa&y=pa&r=no&chartType=beeswarm&sort=xwoba&"
    "sortDir=desc&csv=true"
)


PARK_HR_FACTORS = {
    "Angel Stadium": 101,
    "Busch Stadium": 90,
    "Chase Field": 101,
    "Citi Field": 95,
    "Citizens Bank Park": 112,
    "Coors Field": 120,
    "Dodger Stadium": 104,
    "Fenway Park": 102,
    "George M. Steinbrenner Field": 105,
    "Great American Ball Park": 121,
    "Kauffman Stadium": 92,
    "Las Vegas Ballpark": 100,
    "loanDepot park": 89,
    "Minute Maid Park": 103,
    "Nationals Park": 101,
    "Oracle Park": 85,
    "Oriole Park at Camden Yards": 108,
    "Petco Park": 91,
    "PNC Park": 94,
    "Progressive Field": 100,
    "Rate Field": 98,
    "Rogers Centre": 105,
    "Sutter Health Park": 106,
    "T-Mobile Park": 96,
    "Target Field": 99,
    "Truist Park": 106,
    "Wrigley Field": 104,
    "Yankee Stadium": 119,
}


PARK_WEATHER = {
    "Angel Stadium": {"lat": 33.8003, "lon": -117.8827, "name": "Anaheim, CA"},
    "American Family Field": {"lat": 43.0280, "lon": -87.9712, "name": "Milwaukee, WI"},
    "Busch Stadium": {"lat": 38.6226, "lon": -90.1928, "name": "St. Louis, MO"},
    "Chase Field": {"lat": 33.4455, "lon": -112.0667, "name": "Phoenix, AZ"},
    "Citi Field": {"lat": 40.7571, "lon": -73.8458, "name": "Queens, NY"},
    "Citizens Bank Park": {"lat": 39.9061, "lon": -75.1665, "name": "Philadelphia, PA"},
    "Comerica Park": {"lat": 42.3390, "lon": -83.0485, "name": "Detroit, MI"},
    "Coors Field": {"lat": 39.7559, "lon": -104.9942, "name": "Denver, CO"},
    "Daikin Park": {"lat": 29.7573, "lon": -95.3555, "name": "Houston, TX"},
    "Dodger Stadium": {"lat": 34.0739, "lon": -118.2400, "name": "Los Angeles, CA"},
    "Fenway Park": {"lat": 42.3467, "lon": -71.0972, "name": "Boston, MA"},
    "George M. Steinbrenner Field": {"lat": 27.9799, "lon": -82.5072, "name": "Tampa, FL"},
    "Globe Life Field": {"lat": 32.7473, "lon": -97.0842, "name": "Arlington, TX"},
    "Great American Ball Park": {"lat": 39.0979, "lon": -84.5082, "name": "Cincinnati, OH"},
    "Kauffman Stadium": {"lat": 39.0517, "lon": -94.4803, "name": "Kansas City, MO"},
    "Las Vegas Ballpark": {"lat": 36.1587, "lon": -115.3330, "name": "Las Vegas, NV"},
    "loanDepot park": {"lat": 25.7781, "lon": -80.2197, "name": "Miami, FL"},
    "Minute Maid Park": {"lat": 29.7573, "lon": -95.3555, "name": "Houston, TX"},
    "Nationals Park": {"lat": 38.8730, "lon": -77.0074, "name": "Washington, DC"},
    "Oracle Park": {"lat": 37.7786, "lon": -122.3893, "name": "San Francisco, CA"},
    "Oriole Park at Camden Yards": {"lat": 39.2840, "lon": -76.6217, "name": "Baltimore, MD"},
    "Petco Park": {"lat": 32.7073, "lon": -117.1573, "name": "San Diego, CA"},
    "PNC Park": {"lat": 40.4469, "lon": -80.0057, "name": "Pittsburgh, PA"},
    "Progressive Field": {"lat": 41.4962, "lon": -81.6852, "name": "Cleveland, OH"},
    "Rate Field": {"lat": 41.8300, "lon": -87.6338, "name": "Chicago, IL"},
    "Rogers Centre": {"lat": 43.6414, "lon": -79.3894, "name": "Toronto, ON"},
    "Sutter Health Park": {"lat": 38.5804, "lon": -121.5139, "name": "West Sacramento, CA"},
    "T-Mobile Park": {"lat": 47.5914, "lon": -122.3325, "name": "Seattle, WA"},
    "Target Field": {"lat": 44.9817, "lon": -93.2776, "name": "Minneapolis, MN"},
    "Truist Park": {"lat": 33.8907, "lon": -84.4677, "name": "Atlanta, GA"},
    "Tropicana Field": {"lat": 27.7682, "lon": -82.6534, "name": "St. Petersburg, FL"},
    "UNIQLO Field at Dodger Stadium": {"lat": 34.0739, "lon": -118.2400, "name": "Los Angeles, CA"},
    "Wrigley Field": {"lat": 41.9484, "lon": -87.6553, "name": "Chicago, IL"},
    "Yankee Stadium": {"lat": 40.8296, "lon": -73.9262, "name": "Bronx, NY"},
}


FIELDS = [
    "hitter_id",
    "player",
    "team",
    "opponent",
    "game_start_time",
    "game_status",
    "batting_order",
    "pitcher",
    "pitcher_id",
    "pitcher_hand",
    "hitter_hand",
    "barrel_pct",
    "iso",
    "avg_exit_velocity",
    "ev50",
    "xslg",
    "xiso",
    "xwoba",
    "bat_speed",
    "fast_swing_pct",
    "pull_pct",
    "fb_pct",
    "hard_hit_pct",
    "hr_total",
    "pitcher_barrel_pct_allowed",
    "pitcher_hard_hit_pct_allowed",
    "pitcher_avg_exit_velocity_allowed",
    "pitcher_xslg_allowed",
    "pitcher_xiso_allowed",
    "pitcher_fb_pct_allowed",
    "pitcher_hr_allowed",
    "pitcher_hr_allowed_vs_lhh",
    "pitcher_hr_allowed_vs_rhh",
    "ballpark",
    "park_hr_factor",
    "weather_temp",
    "wind_speed",
    "wind_direction",
    "weather_source",
    "weather_url",
    "weather_humidity",
    "weather_precip_pct",
    "confirmed_lineup",
    "rotowire_confirmed_lineup",
    "rotowire_batting_order",
    "rotowire_player_found",
    "lineup_disagreement",
    "lineup_sources_used",
    "source_warnings",
    "stat_years_used",
    "bvp_pa",
    "bvp_hr",
    "bvp_note",
    "recent_games",
    "recent_hits",
    "recent_abs",
    "recent_hr",
    "recent_form_note",
    "split_matchup_note",
    "pitch_mix_note",
    "public_attention",
    "odds",
]


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def safe_fetch_json(url):
    try:
        return fetch_json(url)
    except Exception:
        return {}


def fetch_csv(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        text = response.read().decode("utf-8-sig")
    return list(csv.DictReader(text.splitlines()))


def fetch_text(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def clean_name(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9 ]", "", value.lower())
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"\s+(jr|sr|ii|iii|iv)$", "", value)
    return value


def strip_tags(value):
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def weather_parts(weather):
    temp = weather.get("temp", "")
    wind = weather.get("wind", "")
    speed_match = re.search(r"(\d+)", wind)
    speed = speed_match.group(1) if speed_match else ""
    direction = wind.split(",", 1)[1].strip() if "," in wind else wind
    return temp, speed, direction


def weather_url(lat, lon):
    return f"https://forecast.weather.gov/MapClick.php?lat={lat:.4f}&lon={lon:.4f}"


def game_hour_iso(game_date):
    try:
        dt = datetime.fromisoformat(str(game_date).replace("Z", "+00:00"))
    except ValueError:
        return ""
    return dt.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z")


def open_meteo_weather(venue, game_date):
    park = PARK_WEATHER.get(venue)
    if not park:
        return {}
    lat = park["lat"]
    lon = park["lon"]
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&hourly=temperature_2m,relative_humidity_2m,precipitation_probability,wind_speed_10m,wind_direction_10m"
        "&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch&timezone=UTC"
        "&forecast_days=2"
    )
    data = safe_fetch_json(url)
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    if not times:
        return {"weather_url": weather_url(lat, lon), "weather_source": "NOAA link only"}

    target = game_hour_iso(game_date)
    target_key = target.replace("Z", "")
    try:
        index = times.index(target_key)
    except ValueError:
        index = 0

    wind_dir = hourly.get("wind_direction_10m", [""])[index]
    return {
        "weather_temp": round(float(hourly.get("temperature_2m", [""])[index])),
        "wind_speed": round(float(hourly.get("wind_speed_10m", [""])[index])),
        "wind_direction": f"{round(float(wind_dir))} deg",
        "weather_humidity": round(float(hourly.get("relative_humidity_2m", [""])[index])),
        "weather_precip_pct": round(float(hourly.get("precipitation_probability", [""])[index])),
        "weather_source": "Open-Meteo forecast; MLB fallback",
        "weather_url": weather_url(lat, lon),
    }


def handedness(player_ids):
    if not player_ids:
        return {}
    url = "https://statsapi.mlb.com/api/v1/people?personIds=" + ",".join(
        str(player_id) for player_id in sorted(player_ids)
    )
    data = fetch_json(url)
    result = {}
    for person in data.get("people", []):
        result[person["id"]] = {
            "bat": person.get("batSide", {}).get("code", ""),
            "pitch": person.get("pitchHand", {}).get("code", ""),
        }
    return result


def recent_hitting_form(player_id, season):
    if not player_id:
        return {
            "recent_games": "",
            "recent_hits": "",
            "recent_abs": "",
            "recent_hr": "",
            "recent_form_note": "Recent form unavailable",
        }
    data = safe_fetch_json(
        "https://statsapi.mlb.com/api/v1/people/"
        f"{player_id}/stats?stats=gameLog&group=hitting&season={season}"
    )
    stats = data.get("stats", [])
    splits = stats[0].get("splits", []) if stats else []
    games = sorted(
        splits,
        key=lambda row: row.get("date", ""),
        reverse=True,
    )[:7]
    hits = sum(int(row.get("stat", {}).get("hits", 0) or 0) for row in games)
    at_bats = sum(int(row.get("stat", {}).get("atBats", 0) or 0) for row in games)
    homers = sum(int(row.get("stat", {}).get("homeRuns", 0) or 0) for row in games)
    if not games:
        note = "Recent form unavailable"
    elif homers >= 2:
        note = f"Hot streak: {homers} HR in last {len(games)} games"
    elif at_bats and hits / at_bats >= 0.320:
        note = f"Contact streak: {hits}/{at_bats} over last {len(games)} games"
    else:
        note = f"Last {len(games)} games: {hits}/{at_bats}, {homers} HR"
    return {
        "recent_games": len(games),
        "recent_hits": hits,
        "recent_abs": at_bats,
        "recent_hr": homers,
        "recent_form_note": note,
    }


def savant_maps(year):
    batters = {row["player_id"]: row for row in fetch_csv(BATTER_URL.format(year=year))}
    pitchers = {row["player_id"]: row for row in fetch_csv(PITCHER_URL.format(year=year))}
    return batters, pitchers


def numeric(value):
    try:
        if value in ("", None):
            return None
        return float(str(value).replace("%", ""))
    except ValueError:
        return None


def blend_rows(rows_by_year, current_year):
    available = [(year, row) for year, row in rows_by_year.items() if row]
    if not available:
        return {}, ""

    base_year, base = max(available)
    blended = dict(base)
    weighted_columns = set().union(*(row.keys() for _, row in available))
    for column in weighted_columns:
        values = []
        for year, row in available:
            value = numeric(row.get(column))
            if value is None:
                continue
            values.append((value, HISTORY_WEIGHTS.get(year - current_year, 0)))
        if not values:
            continue
        weight_total = sum(weight for _, weight in values)
        if weight_total:
            blended[column] = round(sum(value * weight for value, weight in values) / weight_total, 4)

    years_used = "/".join(str(year) for year, _ in sorted(available, reverse=True))
    return blended, years_used


def historical_savant_maps(year):
    current_year = int(year)
    batter_years = {}
    pitcher_years = {}
    for offset in HISTORY_WEIGHTS:
        stat_year = current_year + offset
        batters, pitchers = savant_maps(str(stat_year))
        for player_id, row in batters.items():
            batter_years.setdefault(player_id, {})[stat_year] = row
        for player_id, row in pitchers.items():
            pitcher_years.setdefault(player_id, {})[stat_year] = row

    batters = {}
    batter_years_used = {}
    for player_id, rows_by_year in batter_years.items():
        batters[player_id], batter_years_used[player_id] = blend_rows(rows_by_year, current_year)

    pitchers = {}
    pitcher_years_used = {}
    for player_id, rows_by_year in pitcher_years.items():
        pitchers[player_id], pitcher_years_used[player_id] = blend_rows(rows_by_year, current_year)

    return batters, pitchers, batter_years_used, pitcher_years_used


def savant_display_name(row):
    raw = row.get("last_name, first_name", "")
    if "," not in raw:
        return raw.strip()
    last, first = raw.split(",", 1)
    return f"{first.strip()} {last.strip()}".strip()


def parse_rotowire_lineups():
    try:
        text = fetch_text(ROTOWIRE_LINEUPS_URL)
    except Exception as exc:
        return {}, {}, f"RotoWire unavailable: {type(exc).__name__}"

    lineups = {}
    team_lineups = {}
    boxes = re.findall(r'<div class="lineup__box">(.*?)<div class="lineup__bottom">', text, flags=re.S)
    if not boxes:
        boxes = re.findall(r'<div class="lineup__box">(.*?)(?=<div class="lineup__box">|</main>|</body>)', text, flags=re.S)

    for box in boxes:
        teams = re.findall(r'<div class="lineup__abbr">([^<]+)</div>', box)
        lists = re.findall(r'<ul class="lineup__list is-(visit|home)">(.*?)</ul>', box, flags=re.S)
        side_to_team = {}
        if len(teams) >= 2:
            side_to_team = {"visit": teams[0].strip().upper(), "home": teams[1].strip().upper()}

        for side, lineup_html in lists:
            team = side_to_team.get(side)
            if not team:
                continue

            status_match = re.search(r'<li class="lineup__status([^"]*)">(.*?)</li>', lineup_html, flags=re.S)
            status_classes = status_match.group(1) if status_match else ""
            status_text = strip_tags(status_match.group(2)) if status_match else ""
            confirmed_status = "Yes" if "is-confirmed" in status_classes or "Confirmed" in status_text else "No"

            players = []
            for match in re.finditer(r'<li class="lineup__player">(.*?)</li>', lineup_html, flags=re.S):
                player_html = match.group(1)
                title = re.search(r'<a[^>]+title="([^"]+)"', player_html)
                name = html.unescape(title.group(1)).strip() if title else strip_tags(player_html)
                if name:
                    players.append(name)

            for order, name in enumerate(players[:9], start=1):
                team_lineups.setdefault(team, []).append(
                    {
                        "name": name,
                        "order": order,
                        "rotowire_confirmed_lineup": confirmed_status,
                    }
                )
                lineups[(team, clean_name(name))] = {
                    "rotowire_batting_order": order,
                    "rotowire_confirmed_lineup": confirmed_status,
                    "rotowire_player_found": "Yes",
                }

    warning = "" if lineups else "RotoWire parsed no lineups"
    return lineups, team_lineups, warning


def schedule(run_date):
    return fetch_json(
        "https://statsapi.mlb.com/api/v1/schedule"
        f"?sportId=1&date={run_date}&hydrate=probablePitcher,team"
    )


def include_game(game, mode):
    state = game["status"]["detailedState"].lower()
    if mode == "all":
        return "final" not in state
    if mode == "upcoming":
        return any(word in state for word in ["pre-game", "scheduled", "warmup"])
    return "final" not in state


def game_context(game_pk):
    feed = fetch_json(f"https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live")
    box = fetch_json(f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore")
    venue = feed["gameData"].get("venue", {}).get("name", "")
    temp, wind_speed, wind_direction = weather_parts(feed["gameData"].get("weather", {}))
    forecast = open_meteo_weather(venue, feed["gameData"].get("datetime", {}).get("dateTime", ""))
    if not forecast:
        park = PARK_WEATHER.get(venue)
        forecast = {
            "weather_source": "MLB Stats API weather feed",
            "weather_url": weather_url(park["lat"], park["lon"]) if park else "",
            "weather_humidity": "",
            "weather_precip_pct": "",
        }
    return box, {
        "ballpark": venue,
        "park_hr_factor": PARK_HR_FACTORS.get(venue, 100),
        "weather_temp": forecast.get("weather_temp", temp),
        "wind_speed": forecast.get("wind_speed", wind_speed),
        "wind_direction": wind_direction or forecast.get("wind_direction", ""),
        "weather_source": forecast.get("weather_source", "MLB Stats API weather feed"),
        "weather_url": forecast.get("weather_url", ""),
        "weather_humidity": forecast.get("weather_humidity", ""),
        "weather_precip_pct": forecast.get("weather_precip_pct", ""),
    }


def pitcher_for_side(game, side):
    other_side = "home" if side == "away" else "away"
    return game["teams"][other_side].get("probablePitcher", {})


def default(value, fallback=""):
    return value if value not in (None, "") else fallback


def split_matchup_note(hitter_hand, pitcher_hand, pitcher_row):
    hitter = (hitter_hand or "").upper()
    pitcher = (pitcher_hand or "").upper()
    barrel = numeric(pitcher_row.get("barrel_batted_rate")) or 0
    hr_allowed = numeric(pitcher_row.get("home_run")) or 0
    if hitter == "S":
        side = "switch hitter"
    elif hitter and pitcher and hitter != pitcher:
        side = "platoon edge"
    elif hitter and pitcher:
        side = "same-side matchup"
    else:
        side = "handedness incomplete"
    return f"{side}; pitcher baseline {barrel:.1f}% barrel, {hr_allowed:.1f} HR allowed"


def pitch_mix_note(hitter_row, pitcher_row):
    hitter_ev = numeric(hitter_row.get("exit_velocity_avg")) or 0
    hitter_pull = numeric(hitter_row.get("pull_percent")) or 0
    hitter_fb = numeric(hitter_row.get("flyballs_percent")) or 0
    pitcher_fb = numeric(pitcher_row.get("flyballs_percent")) or 0
    if hitter_ev >= 92 and hitter_pull >= 38 and hitter_fb >= 30:
        hitter_note = "lift-pull EV profile"
    elif hitter_ev >= 92:
        hitter_note = "EV profile"
    elif hitter_fb >= 35:
        hitter_note = "fly-ball profile"
    else:
        hitter_note = "neutral batted-ball profile"
    if pitcher_fb >= 30:
        pitcher_note = "pitcher allows elevated contact"
    else:
        pitcher_note = "pitcher fly-ball pressure modest"
    return f"{hitter_note}; {pitcher_note}"


def build_rows(run_date, mode):
    year = run_date[:4]
    batter_stats, pitcher_stats, batter_years_used, pitcher_years_used = historical_savant_maps(year)
    batter_stats_by_name = {
        clean_name(savant_display_name(row)): (player_id, row)
        for player_id, row in batter_stats.items()
    }
    rotowire_lineups, rotowire_team_lineups, rotowire_warning = parse_rotowire_lineups()
    games = [
        game
        for day in schedule(run_date).get("dates", [])
        for game in day.get("games", [])
        if include_game(game, mode)
    ]

    player_ids = set()
    game_boxes = []
    for game in games:
        box, context = game_context(game["gamePk"])
        game_boxes.append((game, box, context))
        for side in ("away", "home"):
            pitcher = pitcher_for_side(game, side)
            if pitcher.get("id"):
                player_ids.add(pitcher["id"])
            batters = box["teams"][side].get("batters", [])[:9]
            if batters:
                for player_id in batters:
                    player_ids.add(player_id)
                continue

            team = box["teams"][side]["team"]["abbreviation"]
            for projected in rotowire_team_lineups.get(team, [])[:9]:
                player_id, _ = batter_stats_by_name.get(clean_name(projected["name"]), ("", {}))
                if str(player_id).isdigit():
                    player_ids.add(int(player_id))

    hands = handedness(player_ids)
    recent_form = {
        player_id: recent_hitting_form(player_id, year)
        for player_id in player_ids
        if str(player_id).isdigit()
    }
    rows = []
    for game, box, context in game_boxes:
        for side in ("away", "home"):
            team = box["teams"][side]["team"]["abbreviation"]
            opponent_side = "home" if side == "away" else "away"
            opponent = box["teams"][opponent_side]["team"]["abbreviation"]
            pitcher = pitcher_for_side(game, side)
            pitcher_id = str(pitcher.get("id", ""))
            pitcher_row = pitcher_stats.get(pitcher_id, {})
            pitcher_history_years = pitcher_years_used.get(pitcher_id, "")

            mlb_batters = box["teams"][side].get("batters", [])[:9]
            entries = []
            if mlb_batters:
                for order, hitter_id in enumerate(mlb_batters, start=1):
                    player = box["teams"][side]["players"].get(f"ID{hitter_id}", {})
                    entries.append(
                        {
                            "order": order,
                            "player_id": str(hitter_id),
                            "player_name": player.get("person", {}).get("fullName", ""),
                            "confirmed_lineup": "Yes",
                            "lineup_sources_used": "MLB Stats API; RotoWire",
                        }
                    )
            else:
                for projected in rotowire_team_lineups.get(team, [])[:9]:
                    player_id, _ = batter_stats_by_name.get(clean_name(projected["name"]), ("", {}))
                    entries.append(
                        {
                            "order": projected["order"],
                            "player_id": str(player_id),
                            "player_name": projected["name"],
                            "confirmed_lineup": "No",
                            "lineup_sources_used": "RotoWire projected lineup; MLB probable pitchers",
                        }
                    )

            for entry in entries:
                order = entry["order"]
                hitter_id = entry["player_id"]
                hitter_row = batter_stats.get(str(hitter_id), {})
                hitter_history_years = batter_years_used.get(str(hitter_id), "")
                if not hitter_row:
                    matched_id, hitter_row = batter_stats_by_name.get(clean_name(entry["player_name"]), ("", {}))
                    hitter_history_years = batter_years_used.get(str(matched_id), hitter_history_years)
                player_name = entry["player_name"]
                rotowire = rotowire_lineups.get((team, clean_name(player_name)), {})
                rotowire_order = rotowire.get("rotowire_batting_order", "")
                rotowire_confirmed = rotowire.get("rotowire_confirmed_lineup", "")
                rotowire_found = rotowire.get("rotowire_player_found", "No")
                disagreements = []
                if entry["confirmed_lineup"] == "No":
                    disagreements.append("lineup projected / unconfirmed")
                if entry["confirmed_lineup"] == "Yes" and rotowire_confirmed and rotowire_confirmed != "Yes":
                    disagreements.append("RotoWire not confirmed")
                if rotowire_order and int(rotowire_order) != order:
                    disagreements.append(f"order MLB {order} vs RotoWire {rotowire_order}")
                if entry["confirmed_lineup"] == "Yes" and not rotowire_order:
                    disagreements.append("not found on RotoWire")

                source_warnings = []
                if rotowire_warning:
                    source_warnings.append(rotowire_warning)
                if disagreements:
                    source_warnings.extend(disagreements)
                hitter_hand = hands.get(int(hitter_id), {}).get("bat", "") if str(hitter_id).isdigit() else ""
                pitcher_hand = hands.get(pitcher.get("id"), {}).get("pitch", "")
                form = recent_form.get(int(hitter_id), {}) if str(hitter_id).isdigit() else {
                    "recent_games": "",
                    "recent_hits": "",
                    "recent_abs": "",
                    "recent_hr": "",
                    "recent_form_note": "Recent form unavailable",
                }

                rows.append(
                    {
                        "hitter_id": hitter_id,
                        "player": player_name,
                        "team": team,
                        "opponent": opponent,
                        "game_start_time": game.get("gameDate", ""),
                        "game_status": game.get("status", {}).get("detailedState", ""),
                        "pitcher": pitcher.get("fullName", ""),
                        "pitcher_id": pitcher_id,
                        "hitter_hand": hitter_hand,
                        "pitcher_hand": pitcher_hand,
                        "barrel_pct": hitter_row.get("barrel_batted_rate", ""),
                        "iso": hitter_row.get("isolated_power", hitter_row.get("xiso", "")),
                        "avg_exit_velocity": hitter_row.get("exit_velocity_avg", ""),
                        "ev50": hitter_row.get("avg_best_speed", ""),
                        "xslg": hitter_row.get("xslg", ""),
                        "xiso": hitter_row.get("xiso", ""),
                        "xwoba": hitter_row.get("xwoba", ""),
                        "bat_speed": hitter_row.get("avg_swing_speed", ""),
                        "fast_swing_pct": hitter_row.get("fast_swing_rate", ""),
                        "pull_pct": hitter_row.get("pull_percent", ""),
                        "fb_pct": hitter_row.get("flyballs_percent", ""),
                        "hard_hit_pct": hitter_row.get("hard_hit_percent", ""),
                        "hr_total": hitter_row.get("home_run", ""),
                        "pitcher_barrel_pct_allowed": pitcher_row.get("barrel_batted_rate", ""),
                        "pitcher_hard_hit_pct_allowed": pitcher_row.get("hard_hit_percent", ""),
                        "pitcher_avg_exit_velocity_allowed": pitcher_row.get("exit_velocity_avg", ""),
                        "pitcher_xslg_allowed": pitcher_row.get("xslg", ""),
                        "pitcher_xiso_allowed": pitcher_row.get("xiso", ""),
                        "pitcher_fb_pct_allowed": pitcher_row.get("flyballs_percent", ""),
                        "pitcher_hr_allowed": pitcher_row.get("home_run", ""),
                        "pitcher_hr_allowed_vs_lhh": pitcher_row.get("home_run", ""),
                        "pitcher_hr_allowed_vs_rhh": pitcher_row.get("home_run", ""),
                        "batting_order": order,
                        "confirmed_lineup": entry["confirmed_lineup"],
                        "rotowire_confirmed_lineup": rotowire_confirmed,
                        "rotowire_batting_order": rotowire_order,
                        "rotowire_player_found": rotowire_found,
                        "lineup_disagreement": "Yes" if disagreements else "No",
                        "lineup_sources_used": entry["lineup_sources_used"],
                        "source_warnings": "; ".join(source_warnings),
                        "stat_years_used": f"H:{hitter_history_years} P:{pitcher_history_years}",
                        "bvp_pa": "",
                        "bvp_hr": "",
                        "bvp_note": "Direct BvP not yet weighted; 2026/2025 Statcast baseline active",
                        **form,
                        "split_matchup_note": split_matchup_note(hitter_hand, pitcher_hand, pitcher_row),
                        "pitch_mix_note": pitch_mix_note(hitter_row, pitcher_row),
                        "public_attention": "",
                        "odds": "",
                        **context,
                    }
                )
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--mode", choices=["upcoming", "all"], default="upcoming")
    parser.add_argument("--output", default=str(OUTPUT_PATH))
    args = parser.parse_args()

    rows = build_rows(args.date, args.mode)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    daily_output = DAILY_DIR / f"collected_slate_{args.date}_{args.mode}.csv"
    with daily_output.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} hitters to {output}")
    print(f"Saved daily collected slate to {daily_output}")


if __name__ == "__main__":
    main()
