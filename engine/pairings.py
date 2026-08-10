from __future__ import annotations

from itertools import combinations

from .utils import confirmed, number


MIN_MODEL_EDGE = {2: 5.7, 3: 5.8, 4: 5.9}


def player_game(row: dict) -> str:
    teams = sorted([str(row.get("team")), str(row.get("opponent"))])
    return f"{teams[0]}-{teams[1]}-{row.get('ballpark')}"


def sheet_match(row: dict) -> bool:
    return "Sheet Match" in row.get("labels", []) or number(row.get("sheet_score"), 50) >= 68


def carry_signal(row: dict) -> bool:
    return number(row.get("sheet_carry_score"), number(row.get("components", {}).get("sheet_carry"), 50)) >= 68


def cold_streak(row: dict) -> bool:
    games = number(row.get("recent_games"))
    at_bats = number(row.get("recent_abs"))
    hits = number(row.get("recent_hits"))
    homers = number(row.get("recent_hr"))
    if games < 5 or at_bats < 12:
        return False
    return homers == 0 and hits / max(at_bats, 1) < 0.170


def tiny_sheet_sample(row: dict) -> bool:
    pa = number(row.get("sheet_pm_pa"))
    barrel = number(row.get("sheet_barrel_pct"))
    return 0 < pa < 25 and barrel >= 20


def park_resistance(row: dict) -> bool:
    sheet_env = number(row.get("sheet_hr_env"), 0)
    env = number(row.get("environment_score"), 50)
    return sheet_env <= -8 or env < 47


def leg_reliability(row: dict) -> float:
    score = number(row.get("edge_index")) * 10
    score += max(-4, min(8, (number(row.get("sheet_score"), 50) - 50) * 0.16))
    score += max(-3, min(4, (number(row.get("recent_form_score"), 50) - 50) * 0.05))

    order = number(row.get("batting_order"), 9)
    if confirmed(row.get("confirmed_lineup")):
        score += 3.0
    else:
        score -= 2.5
    if order <= 4:
        score += 2.0
    elif order >= 6:
        score -= 2.5
    if sheet_match(row):
        score += 3.0
    if carry_signal(row):
        score += 2.5
    if tiny_sheet_sample(row):
        score -= 4.0
    if park_resistance(row) and not carry_signal(row):
        score -= 3.0
    if cold_streak(row) and not sheet_match(row):
        score -= 3.0
    if row.get("volatility") == "High":
        score -= 3.0
    elif row.get("volatility") == "Low":
        score += 1.0
    return round(score, 1)


def one_off_flags(row: dict) -> list[str]:
    flags: list[str] = []
    if not confirmed(row.get("confirmed_lineup")):
        flags.append("lineup/void risk")
    if tiny_sheet_sample(row):
        flags.append("tiny sheet sample")
    if park_resistance(row) and not carry_signal(row):
        flags.append("park resistance")
    if sheet_match(row) and not carry_signal(row):
        flags.append("weak carry-through")
    if cold_streak(row):
        flags.append("cold streak")
    if number(row.get("batting_order"), 9) >= 6:
        flags.append("lower-order risk")
    if number(row.get("pitcher_score")) < 48 and not sheet_match(row):
        flags.append("pitcher resistance")
    if not sheet_match(row) and number(row.get("edge_index")) < 6.2:
        flags.append("weak sheet/model agreement")
    return flags


def severe_one_off_flags(row: dict) -> list[str]:
    severe: list[str] = []
    for flag in one_off_flags(row):
        if flag in {"tiny sheet sample", "lower-order risk", "weak sheet/model agreement"}:
            severe.append(flag)
        elif flag == "park resistance" and not sheet_match(row):
            severe.append(flag)
        elif flag == "weak carry-through" and row.get("volatility") == "High":
            severe.append(flag)
    return severe


def pairing_type(group: tuple[dict, ...]) -> str:
    games = [player_game(row) for row in group]
    same_game = len(set(games)) < len(games)
    avg_env = sum(number(row.get("environment_score")) for row in group) / len(group)
    sleeper = any("Sleeper" in row.get("labels", []) for row in group)
    sheet_count = sum(1 for row in group if sheet_match(row))
    if sheet_count == len(group):
        return "Sheet Consensus"
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
    sheet_count = sum(1 for row in group if sheet_match(row))
    carry_count = sum(1 for row in group if carry_signal(row))
    weak_legs = sum(1 for row in group if leg_reliability(row) < 58)
    same_game_count = size - unique_games

    score = avg_edge
    score += unique_games * 0.12
    score += confirmed_count * 0.08
    score += sheet_count * 0.10
    score += carry_count * 0.09
    score += min(0.30, sum(leg_reliability(row) for row in group) / size / 250)
    score -= max(0, 6.2 - min_edge) * 0.35
    score -= high_vol * 0.18
    score -= weak_legs * (0.18 if size == 2 else 0.28)

    if same_game_count:
        if avg_env >= 68:
            score += 0.25
        else:
            score -= 0.55

    if size == 4:
        score -= 0.35
        if weak_legs:
            score -= 0.35
        if carry_count < 3:
            score -= 0.30
    return round(score, 2)


def viable_for_size(row: dict, size: int) -> bool:
    edge = number(row.get("edge_index"))
    reliability = leg_reliability(row)
    if edge < MIN_MODEL_EDGE[size] and not (sheet_match(row) and reliability >= 64):
        return False
    if size == 2:
        return reliability >= 54
    if size == 3:
        return reliability >= 56 or sheet_match(row)
    if row.get("volatility") == "High":
        return False
    if severe_one_off_flags(row):
        return sheet_match(row) and reliability >= 66
    if size == 4 and sheet_match(row) and not carry_signal(row):
        return reliability >= 66
    return reliability >= 59


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
        weak_legs = [row for row in group if leg_reliability(row) < 58]
        severe_legs = [row for row in group if severe_one_off_flags(row)]
        if size == 3 and len(weak_legs) > 1:
            continue
        if size == 3 and len(severe_legs) > 1:
            continue
        if size == 4 and weak_legs:
            continue
        if size == 4 and severe_legs:
            continue
        if size == 4 and sum(1 for row in group if carry_signal(row)) < 3:
            continue
        if size >= 3 and sum(1 for row in group if not confirmed(row.get("confirmed_lineup"))) == size:
            if sum(1 for row in group if sheet_match(row)) < size - 1:
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
    if any("Sheet Match" in row.get("labels", []) for row in group):
        reasons.append("sheet/model agreement")
    if any(carry_signal(row) for row in group):
        reasons.append("sheet carry-through")
    if any("Sleeper" in row.get("labels", []) for row in group):
        reasons.append("sleeper leverage")
    reliability = [leg_reliability(row) for row in group]
    if min(reliability) >= 62 and not any(severe_one_off_flags(row) for row in group):
        reasons.append("no obvious one-off leg")
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
        "leg_reliability": " / ".join(
            f"{row.get('player')}: {leg_reliability(row)}" for row in group
        ),
        "one_off_flags": " / ".join(
            f"{row.get('player')}: {', '.join(one_off_flags(row)) or 'clean'}" for row in group
        ),
    }


def pairing_volatility(group: tuple[dict, ...]) -> str:
    values = [row.get("volatility") for row in group]
    if values.count("High") >= 2 or len(group) >= 4:
        return "High"
    if "High" in values or "Medium" in values:
        return "Medium"
    return "Low"
