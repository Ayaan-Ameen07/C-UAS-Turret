# Confirmed parts and measurements

Single source of truth for parts I have physically checked. If another doc
disagrees with this one, ask Aru. Last updated: Nov 9, 2026.

| Item | Value | How I know |
|---|---|---|
| Motor kits | 2x S42C closed-loop stepper, one 6-pin connector each | Checked on the bench |
| Motor plug | 6 pins, 12.7 mm from pin 1 to pin 6, so 2.54 mm pitch (XH2.54 style) | Ruler, Nov 9 |
| Motor cable | One 6-wire flat ribbon, plug on each end | Looked at it, Nov 9 |
| Lab adapter (loan) | Neewer NW-120300D2, 12 V, 3.0 A, center-positive from the label (not measured) | Label, Nov 9 |
| Adapter no-load output | 12.48 V | Multimeter, Nov 9 |
| Adapter plug | About 5.5 x 2.1 mm (ruler said about 5 mm outer, inner not measurable). Fits the lab DC jack. | Ruler and fit, Nov 9 |
| Fuses | AKOSN automotive blade kit, ATC/ATO standard size, all rated 32 V, 2 A to 40 A | Photo of box, Nov 9 |
| Microcontroller board | ECE-shop loan, Nucleo-144 form factor (returns to ECE at end of semester) | Case label and board |
| Nucleo exact model | **STM32F767ZIT6** on a NUCLEO-F767ZI. The Purdue case label says F746ZG, but the chip on the board is what counts. | Aru read the chip marking, Nov 9 |
| Nucleo size | 144 pin family: same Morpho and ZIO headers across the family | ST Nucleo-144 family |

Why the Nucleo model matters little for the PCB: all Nucleo-144 boards share
the same header layout, so the carrier PCB footprint is the same. It matters
for firmware (timer and pin choices), so confirm before writing code.

## ECE shop loans
Nucleo-144 (NUCLEO-F767ZI), the Neewer 12 V 3 A adapter, USB cables, pin
headers and two transistors all go back to the ECE shop at the **end of the
semester**. That is after the Dec 12 demo, so no replacement board is needed.
Last updated: Nov 10, 2026.

## Orders
- Raspberry Pi 5: the only purchase planned for Nov 10.
