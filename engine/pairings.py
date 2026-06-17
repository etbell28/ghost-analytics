from __future__ import annotations

from itertools import combinations

from .utils import confirmed, number


def player_game(row: dict) -> str:
    teams = sorted([str(row.get("team")), str(row.get("opponent"))])
    return f"{teams[0]}-{teams[1]}-{row.get('ballpark')}"


def pairing_type(group: tuple[dict, ...]) -> str:
    games = [player_game(row) for row in group]
    same_game = len(set(games)) < len(games)
    avg_env = sum(number(row.get("environment_score")) for row in group) / len(group)
    sleeper = any("Sleeper" in row.get("labels", []) for row in group)
    if same_game and avg_env >= 68:
        return "Weather Stack"
    if sleeper:
        return "Sleeper Pair" if len(group) == 2 else "Aggressive 3"
    if len(group) >= 3:
        return "Aggressive 3"
    if all(number(row.get("components", {}).get("hitter_power")) >= 70 for row in group):
        return "Power Pair"
    return "Balanced 2"


def combo_score(group: tuple[dict, ...]) -> float:
    size = len(group)
    avg_edge = sum(number(row.get("edge_index")) for row in group) / size
    min_edge = min(number(row.get("edge_index")) for row in group)
    games = [player_game(row) for row in group]
    unique_games = len(set(games))
    avg_env = sum(number(row.get("environment_score")) for row in group) / size
    confirmed_count = sum(1 for row in group if confirmed(row.get("confirmed_lineup")))
    high_vol = sum(1 for row in group if row.get("volatility") == "High")
    same_game_count = size - unique_games

    score = avg_edge
    score += unique_games * 0.12
    score += confirmed_count * 0.08
    score -= max(0, 6.2 - min_edge) * 0.35
    score -= high_vol * 0.18

    if same_game_count:
        if avg_env >= 68:
            score += 0.25
        else:
            score -= 0.55

    if size == 4:
        score -= 0.35
    return round(score, 2)


def viable_for_size(row: dict, size: int) -> bool:
    edge = number(row.get("edge_index"))
    if size == 2:
        return edge >= 5.7
    if size == 3:
        return edge >= 6.0
    return edge >= 6.5 and row.get("volatility") != "High"


def build_pairings(rows: list[dict], size: int, limit: int = 8) -> list[dict]:
    pool = [row for row in rows if viable_for_size(row, size)]
    pool = sorted(pool, key=lambda row: number(row.get("edge_index")), reverse=True)[:36]
    if size == 4 and len(pool) < 8:
        return []
    if len(pool) < size:
        return []

    combos = []
    for group in combinations(pool, size):
        teams = [row.get("team") for row in group]
        if len(set(teams)) < min(size, 3):
            continue
        cscore = combo_score(group)
        if size == 4 and cscore < 6.7:
            continue
        combos.append((cscore, group))

    selected = []
    exposure: dict[str, int] = {}
    max_exposure = 3 if size == 2 else 2
    for cscore, group in sorted(combos, key=lambda item: item[0], reverse=True):
        names = [str(row.get("player")) for row in group]
        if any(exposure.get(name, 0) >= max_exposure for name in names):
            continue
        selected.append(format_pairing(group, cscore))
        for name in names:
            exposure[name] = exposure.get(name, 0) + 1
        if len(selected) >= limit:
            break
    return selected


def format_pairing(group: tuple[dict, ...], cscore: float) -> dict:
    avg_edge = sum(number(row.get("edge_index")) for row in group) / len(group)
    games = [player_game(row) for row in group]
    reasons = []
    if len(set(games)) == len(games):
        reasons.append("independent games")
    elif sum(number(row.get("environment_score")) for row in group) / len(group) >= 68:
        reasons.append("weather stack logic")
    if any("Pitcher Target" in row.get("labels", []) for row in group):
        reasons.append("pitcher target included")
    if any("Sleeper" in row.get("labels", []) for row in group):
        reasons.append("sleeper leverage")
    if not reasons:
        reasons.append("balanced edge mix")

    return {
        "names": " + ".join(str(row.get("player")) for row in group),
        "teams": " / ".join(f"{row.get('team')} vs {row.get('opponent')}" for row in group),
        "avg_edge": round(avg_edge, 1),
        "combo_score": cscore,
        "type": pairing_type(group),
        "volatility": pairing_volatility(group),
        "labels": " / ".join(", ".join(row.get("labels", [])) for row in group),
        "reason": " · ".join(reasons),
    }


def pairing_volatility(group: tuple[dict, ...]) -> str:
    values = [row.get("volatility") for row in group]
    if values.count("High") >= 2 or len(group) >= 4:
        return "High"
    if "High" in values or "Medium" in values:
        return "Medium"
    return "Low"

