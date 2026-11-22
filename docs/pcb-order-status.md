# Carrier PCB: order status

Last updated: Nov 22, 2026. Everything ships to Purdue (West Lafayette).

## Design
- Board: `pcb/` on `main`, KiCad 10. 2 layers, 150 x 100 mm, 1.6 mm, 1 oz.
- Fab files: `pcb/gerbers.zip` (re-plotted Nov 21 after the review fixes).
- Independent review: **GO** on Nov 21 after one must-fix (Pololu module was under the Nucleo; J3 now has EN on the bottom pin and the module points left, away from the Nucleo).
- 1:1 paper fit with the Nucleo: headers and the 2 mounting holes line up. The Nucleo's other side has no standoff: use an 11 mm spacer there.
- Review exports: `pcb/review/` (ERC, DRC, netlist, BOM, schematic PDF).

## Orders
| What | Where | Status |
|---|---|---|
| Bare PCB x5 (green, lead-free HASL, 1 oz, no assembly) | JLCPCB | Ordered |
| Board parts, 28 lines (incl. spares, Pi 5 Active Cooler, JST XH leads/housings, 2x5 Pi socket, M3 nuts) | Digi-Key | Ordered Nov 21, USPS Ground |
| Pololu D24V50F5 5 V 5 A regulator | Pololu | Ordered Nov 21 |
| 12 V 8 A adapter, 5.5 x 2.5 mm center-positive | Amazon | Ordered. Check the plug is 2.5 mm, not 2.1 |
| microSD 32 GB (Patriot LX) | Amazon | Ordered. Back the card up once the Pi is set up |
| Male-to-female jumper wires, 40 pack | Amazon | Backup only, not needed unless the Nucleo won't stack |

Full line-by-line list with links and prices: `docs/turret_bom.xlsx`, tab **PCB Order (Nov 21)**.

## Part changes vs. older docs
`docs/parts-selection.md` has older rows. These are what was actually ordered:
- Q1: Diodes **DMP3013SFV-7** (PowerDI3333-8), not the TO-252 parts.
- D2: **SMCJ18CA** (not SMCJ15CA), so a 4S LiPo (16.8 V) can use the XT60 pads.
- D3-D5: **red** Kingbright APT2012LSECK/J3-PRV (not green).
- C1: Panasonic **EEU-FR1V102B** (same size and pitch as EEU-FR1V102, which was out of stock).
- Kept the Pololu D24V50F5. A cheaper 3 A Traco buck was rejected: it doesn't fit the 5-pin J3 footprint and 3 A is too little for the Pi 5.

## Bring-up notes (when the board arrives)
- First power-up on a current-limited bench supply, 12 V, 1 A limit.
- Pololu: **EN pin goes on the bottom pin of J3** (the silk says so); module sits over the outline left of J3.
- First motor plug-in with the Nucleo unplugged: check 12 V lands on the motor's VM wire (the S42C plug is an XH look-alike).
- Measure TP4 (5V_PI) under load. Never plug the Pi's USB-C in while J4 is connected.
- The Nucleo and Arducam connect by USB (to the Pi or a laptop), not through the PCB.
