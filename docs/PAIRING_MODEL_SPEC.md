# Pairing Model Spec

Pairings are not just grouped rankings.

## Objective

Create combinations that have a better chance of cashing together by balancing:

- Individual HR edge
- Game correlation
- Weather/park context
- Pitcher vulnerability
- Time remaining
- Lineup confirmation
- Volatility
- Exposure control

## Pairing Inputs

Each player should carry:

- Edge Index
- Power score
- Pitcher target score
- Weather score
- Lineup status
- Start time
- Game status
- Volatility
- Labels
- Odds/price when available

## Pairing Penalties

Apply penalties for:

- Too many unconfirmed hitters
- Too many hitters from games already started
- Repeating the same player across most pairings
- Combining multiple high-volatility plays without enough edge
- Same-game pairing without a real stack reason
- 4-leg combos below edge threshold

## Pairing Bonuses

Apply bonuses for:

- Different games with independent paths
- Same game only when weather/park/pitcher supports stack logic
- One sleeper with one or two stronger anchors
- Confirmed lineup status
- Late-game flexibility
- Strong weather plus pitcher vulnerability agreement

## Exposure Rules

Suggested starting rules:

- A player cannot appear in more than 40% of shown 2-leg pairings.
- A player cannot appear in more than 50% of shown 3-leg pairings.
- A player cannot appear in every 4-leg pairing unless fewer than 5 viable players exist.
- Do not show a 4-leg section if fewer than 8 viable players clear threshold.

## Public Pairing Types

- **Balanced:** best mix of edge and independence.
- **Power Pair:** highest individual HR profile.
- **Weather Stack:** same game or same environment with strong weather support.
- **Sleeper Pair:** includes one lower-profile leverage play.
- **Aggressive:** high upside, higher miss risk.
- **No Play:** displayed when the model refuses to force weak combos.

