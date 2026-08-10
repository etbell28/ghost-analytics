from __future__ import annotations

from dataclasses import dataclass


EASTERN_TZ = "America/New_York"


@dataclass(frozen=True)
class ModelWeights:
    hitter_power: float = 0.32
    pitcher_vulnerability: float = 0.24
    batted_ball_fit: float = 0.14
    environment: float = 0.12
    lineup_opportunity: float = 0.10
    recent_form: float = 0.05
    bvp_pitch_mix: float = 0.03


WEIGHTS = ModelWeights()


PUBLIC_LABELS = [
    "Weather Edge",
    "Hot Bat",
    "EV Edge",
    "Pitcher Target",
    "Sheet Match",
    "Carry Signal",
    "Sleeper",
    "Tough Pitcher",
    "Confirmed",
    "Projected",
    "Watch",
]


LABEL_DEFINITIONS = {
    "Weather Edge": "Park and weather are helping home run conditions: wind, temperature, roof, air density, or HR park factor.",
    "Hot Bat": "Recent form is strong. It matters, but it does not override the matchup model.",
    "EV Edge": "The hitter's batted-ball quality is strong: exit velocity, EV50, hard-hit rate, or barrel rate.",
    "Pitcher Target": "The opposing pitcher is allowing HR-friendly contact, barrels, xSLG, xISO, or split damage.",
    "Sheet Match": "Today's external sheet agrees with GhostIQ on hitter power, pitcher split, or park/weather fit. It is a confirmation signal, not a standalone pick.",
    "Carry Signal": "The sheet profile is strong enough to matter beyond the starting pitcher: power volume, EV/barrel/ISO, park help, and split weakness support late-game HR upside.",
    "Sleeper": "A lower-profile hitter with enough data support to matter, usually with higher volatility.",
    "Tough Pitcher": "The hitter has real power signals, but the opposing pitcher creates resistance.",
    "Confirmed": "The hitter is confirmed in the starting lineup.",
    "Projected": "The hitter is based on projected lineup data and needs confirmation.",
    "Watch": "The hitter has at least one signal but not enough agreement to be a core target.",
}
