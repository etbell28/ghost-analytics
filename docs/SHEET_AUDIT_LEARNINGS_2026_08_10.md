# GhostIQ Sheet Audit - 2026-08-08 to 2026-08-09

## What Was Audited

- Uploaded sheet callouts from August 8 and August 9.
- Official MLB game-feed home run events for the same dates.
- Sheet hits, sheet misses, and official homers that were not in the structured sheet snapshot.

## 2026-08-08

- Sheet-called players tracked: 34
- Sheet-called players who homered: 18
- Sheet-called HR events: 20
- Official HR events: 28
- HR events outside the structured sheet snapshot: 8

Sheet hits:
Ben Rice, Ronald Acuna Jr., Bryce Harper, Trea Turner, Vladimir Guerrero Jr., Brandon Lowe, Ian Happ, Jac Caglianone, Taylor Trammell, Jackson Merrill, Jordan Walker, Jake McCarthy, Corey Seager, Rhys Hoskins, Munetaka Murakami, Angel Genao, Tyler Soderstrom, Henry Bolte

Unlisted official HRs to study:
George Lombard Jr., Nathan Lukes, Eugenio Suárez, Jackson Holliday, Kyle Tucker, Josh Naylor, Victor Mesa Jr., Josh Naylor

## 2026-08-09

- Sheet-called players tracked: 70
- Sheet-called players who homered: 13
- Sheet-called HR events: 16
- Official HR events: 33
- HR events outside the structured sheet snapshot: 17

Sheet hits:
Matt Olson, Trent Grisham, Kyle Schwarber, Ian Happ, Jake Bauers, Jackson Merrill, Ketel Marte, Francisco Alvarez, Colson Montgomery, Alec Burleson, Hunter Goodman, Pete Alonso, Griffin Conine

Unlisted official HRs to study:
Abimelec Ortiz, Luis Robert Jr., Jake Mangum, Jose Siri, Starling Marte, Miguel Amaya, Jackson Chourio, Brooks Lee, Kody Clemens, Brett Sullivan, Colton Cowser, Brandon Nimmo, Tyler O'Neill, Daulton Varsho, Fernando Tatis Jr., Gavin Sheets, Austin Hays

## Learned Logic

1. The sheets are strongest when they combine barrel rate, ISO, EV, pitcher split vulnerability, and plus HR weather/park. Ben Rice, Bryce Harper, Jac Caglianone, Ian Happ, Matt Olson, Kyle Schwarber, Jake Bauers, Alec Burleson, and others fit this pattern.
2. Several sheet hits occurred after the starting pitcher left. The model should not treat the sheet as only a starting-pitcher read. It now adds a Carry Signal for hitters whose power profile can survive bullpen variance.
3. Tiny samples are dangerous for parlays. A hitter can be a straight dart, but tiny-sample sheet pops should not become 4-leg anchors.
4. Bad HR parks should downgrade parlays but not automatically erase elite sheet bats. Corey Seager, Brandon Lowe, Pete Alonso, Griffin Conine, and Ketel Marte showed that strong power can beat a negative environment, especially when the pitcher/bullpen path is weak.
5. The one-off problem is mostly a pairing-construction issue, not a sheet issue. Four-leg slips now require at least three Carry Signal legs and reject severe one-off flags.
6. Unlisted HRs often came from depth hitters, late-inning substitutions, bullpen matchups, or players with incomplete structured sheet rows. This argues for better lineup/bullpen coverage rather than blindly fading sheet misses.

## Engine Changes Made

- Added `sheet_carry_score` to ranking generation.
- Added Carry Signal to the public dashboard labels.
- Added carry-through scoring to the dashboard payload model.
- Tightened pairing logic so 4-leg builds cannot include fragile legs unless the sheet/model/carry case is strong.
- Preserved dated sheet snapshots so future audits do not overwrite prior sheet data.
- Added repeatable audit script: `scripts/audit_sheet_results.py`.

## Practical Pairing Rule Going Forward

For 3-leg slips: use at least two sheet/carry legs and no more than one volatile upside leg.

For 4-leg slips: use at least three sheet/carry legs, avoid tiny samples, and do not force a fourth leg just because the first three are strong.
