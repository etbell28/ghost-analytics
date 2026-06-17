from __future__ import annotations

from .utils import confirmed, number


def public_labels(row: dict) -> list[str]:
    labels: list[str] = []
    power = number(row.get("power_score"))
    pitcher = number(row.get("pitcher_score"))
    env = number(row.get("environment_score"))
    form = number(row.get("recent_form_score"))
    avg_ev = number(row.get("avg_exit_velocity"))
    ev50 = number(row.get("ev50"))
    hard_hit = number(row.get("hard_hit_pct"))
    order = number(row.get("batting_order"), 9)
    edge = number(row.get("edge_index"))

    if confirmed(row.get("confirmed_lineup")):
        labels.append("Confirmed")
    else:
        labels.append("Projected")

    if env >= 68:
        labels.append("Weather Edge")
    if form >= 72:
        labels.append("Hot Bat")
    if avg_ev >= 92 or ev50 >= 103 or hard_hit >= 50:
        labels.append("EV Edge")
    if pitcher >= 64:
        labels.append("Pitcher Target")
    if power >= 72 and pitcher < 48:
        labels.append("Tough Pitcher")
    if edge >= 5.8 and order >= 5:
        labels.append("Sleeper")
    if len(labels) <= 1:
        labels.append("Watch")
    return labels


def label_summary(row: dict) -> str:
    return " + ".join(public_labels(row))

