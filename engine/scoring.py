from __future__ import annotations

from .config import WEIGHTS
from .utils import confirmed, number


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def normalize(value: float, low: float, high: float) -> float:
    if high == low:
        return 0.0
    return clamp((value - low) / (high - low) * 100.0)


def batted_ball_fit(row: dict) -> float:
    barrel = normalize(number(row.get("barrel_pct")), 5, 22)
    ev50 = normalize(number(row.get("ev50")), 98, 108)
    pull = normalize(number(row.get("pull_pct"), 35), 30, 52)
    fb = normalize(number(row.get("fb_pct"), 32), 22, 48)
    fast_swing = normalize(number(row.get("fast_swing_pct"), 45), 30, 75)
    return barrel * 0.32 + ev50 * 0.24 + pull * 0.16 + fb * 0.18 + fast_swing * 0.10


def bvp_pitch_mix_context(row: dict) -> float:
    bvp_pa = number(row.get("bvp_pa"))
    bvp_hr = number(row.get("bvp_hr"))
    base = 50.0
    if bvp_pa >= 8:
        base += min(18, bvp_hr * 8)
    pitch_note = str(row.get("pitch_mix_note") or "").lower()
    if "lift-pull" in pitch_note or "fly-ball" in pitch_note:
        base += 6
    if "modest" in pitch_note:
        base -= 2
    return clamp(base)


def refined_components(row: dict) -> dict[str, float]:
    return {
        "hitter_power": number(row.get("power_score")),
        "pitcher_vulnerability": number(row.get("pitcher_score")),
        "batted_ball_fit": batted_ball_fit(row),
        "environment": number(row.get("environment_score")),
        "lineup_opportunity": number(row.get("lineup_score")),
        "recent_form": number(row.get("recent_form_score"), 50),
        "bvp_pitch_mix": bvp_pitch_mix_context(row),
    }


def internal_score(row: dict) -> float:
    c = refined_components(row)
    score = (
        c["hitter_power"] * WEIGHTS.hitter_power
        + c["pitcher_vulnerability"] * WEIGHTS.pitcher_vulnerability
        + c["batted_ball_fit"] * WEIGHTS.batted_ball_fit
        + c["environment"] * WEIGHTS.environment
        + c["lineup_opportunity"] * WEIGHTS.lineup_opportunity
        + c["recent_form"] * WEIGHTS.recent_form
        + c["bvp_pitch_mix"] * WEIGHTS.bvp_pitch_mix
    )
    if not confirmed(row.get("confirmed_lineup")):
        score -= 2.5
    return clamp(score)


def edge_index(score: float) -> float:
    return round(clamp(score) / 10.0, 1)


def ghost_grade(edge: float) -> str:
    if edge >= 8.8:
        return "A+"
    if edge >= 8.0:
        return "A"
    if edge >= 7.4:
        return "A-"
    if edge >= 6.8:
        return "B+"
    if edge >= 6.2:
        return "B"
    if edge >= 5.6:
        return "B-"
    return "C+"


def volatility(row: dict, score: float) -> str:
    projected_penalty = 1 if not confirmed(row.get("confirmed_lineup")) else 0
    order = number(row.get("batting_order"), 9)
    pitcher = number(row.get("pitcher_score"))
    power = number(row.get("power_score"))
    risk = 0
    if projected_penalty:
        risk += 1
    if order >= 6:
        risk += 1
    if pitcher < 45:
        risk += 1
    if power < 58:
        risk += 1
    if score < 58:
        risk += 1
    if risk >= 3:
        return "High"
    if risk >= 1:
        return "Medium"
    return "Low"


def confidence(row: dict, score: float) -> str:
    if score >= 74 and confirmed(row.get("confirmed_lineup")):
        return "Core"
    if score >= 66:
        return "Strong"
    if score >= 58:
        return "Watch"
    if volatility(row, score) == "High":
        return "Longshot"
    return "Volatile"


def score_row(row: dict) -> dict:
    row = dict(row)
    score = internal_score(row)
    edge = edge_index(score)
    row["ghost_score"] = round(score, 2)
    row["edge_index"] = edge
    row["ghost_grade"] = ghost_grade(edge)
    row["confidence"] = confidence(row, score)
    row["volatility"] = volatility(row, score)
    row["components"] = {key: round(value, 1) for key, value in refined_components(row).items()}
    return row

