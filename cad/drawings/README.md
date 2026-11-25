# 2D drawings (rev A, Nov 25 2026)

`C-UAS-Turret_drawings_revA.pdf` = all 23 sheets in one file (A3 landscape).

| Sheet | Part | Make? |
|---|---|---|
| A00 | Assembly + parts list | - |
| P01 | Floor plate | print |
| P02 | Cover | print |
| P03 | Hatch lid | print |
| P04 | Deck | print |
| P05 | U-bracket | print |
| P06 | Head | print |
| P07 | Head back plate | print |
| P08 | Laser sleeve | print |
| P09 | Motor cover (optional) | print |
| P10 | Nucleo spacer | print |
| R01 | S42C motor (reference model for NX) | bought |

Each part has two sheets: **a-standard** (plain views + iso) and **b-dimensioned** (dimensions + feature table).
Coordinates = NX: X right, Y back, Z up. Origin marked with a crosshair on every sheet.
Drawings are generated from `cad/concept/build.py` by `cad/concept/drawings.py` (build123d), so they match the 3D model.
Bought-part sizes: see `docs/parts/`.
