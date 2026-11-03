# S42C Bring-Up Tests (Oct 25, 2026)

Goal: confirm every wire, pin and voltage on a breadboard so the custom PCB is designed correctly.
Last updated: Oct 29, 2026
Status: IN PROGRESS. Results marked "pending" have not been run yet.

## READ FIRST: the adapter board's printed labels are not hole labels

The small black adapter board (red 6-pin connector in the middle, two rows of through-holes on the sides) is counterintuitive. The words VM, 5V, GND, EN, STP, DIR printed inside the white box name the pins of the **red connector**. They do **not** name the through-holes next to them. Do not wire to a hole based on the word printed beside it.

| What | Status |
|---|---|
| Right column, top to bottom: ring 1 = VM (24 kohm to ground, no short), rings 2 and 8 = GND (about 0.19 ohm to the OLED GND hole), rings 3-7 not used | MEASURED, linked to cable contacts 1 and 3 |
| Left column, top to bottom: ring 1 = EN, ring 7 = STEP, ring 8 = DIR, rings 2-6 not used | MEASURED, linked to cable contacts 4, 5, 6 |
| Red connector pins (manual drawing): VM, NC, GND, EN, CLK (step), DIR | From the manual |
| The adapter's "5V" label sits on the manual's NC pin | Treated as unused |

Never apply power from the printed labels. Use the confirmed hole map in test 1d below.

## Equipment

| Item | Use |
|---|---|
| Keysight EDU34450A DMM | Continuity and voltage checks |
| Keysight EDU36311A supply | Motor power (channel 2 or 3, current limited) |
| Keysight EDU33212A function generator | Step pulses (test 3) |
| Scope | Signal check |
| ECE-loan Nucleo-144 STM32F746ZG | Step/Dir/Enable source (test 5) |
| 2x BIGTREETECH S42C V1.1 kits | Closed-loop motor + driver |

## What the manual confirms

Source: BIGTREETECH S42C User Manual (3-in-1, all versions).

| Item | Value |
|---|---|
| Max current | 1650 mA at 12 V |
| No-load current | 620 mA at 12 V |
| Step/Dir rising edge | 40 ns |
| Microsteps | 1 to 256 (200 steps per turn at 1/1, 3200 at 1/16) |
| Control inputs | Step, Dir, Enable only (no SPI or UART needed) |
| Enable polarity | Set in OLED menu (Normal / Inverted) |
| VM voltage range | 12 V to 24 V. Source: the vendor's product-page "Parameters" graphic. The manual's text leaves this line blank, and the box (S42C V1.1, SKU 1060000545, D/C 2026.07.13) does not print it. First power-up: 12 V with a current limit. |
| First use | Encoder calibration, wait 1-2 minutes |
| Caution | "Do not turn the motor manually after power on" |

### Control connector (from the manual's drawing, top to bottom)

| Pin | Name | Note |
|---|---|---|
| 1 | VM | Motor power |
| 2 | NC | Not connected |
| 3 | GND | Ground |
| 4 | EN | Enable |
| 5 | CLK | Step input (the adapter labels it STP) |
| 6 | DIR | Direction |

### Adapter board labels (corrected Oct 25, 23:20)

The text inside the white box (VM, 5V, GND, EN, STP, DIR) is printed next to the red 6-pin connector. It names the connector pins. It does NOT name the through-holes beside it. Only the corner labels "VM" (top right) and "EN" (top left) look like hole labels.

Hypothesis (matches the resistance readings in test 1c): the holes follow the common A4988 driver footprint.

| Column | Top to bottom | Status |
|---|---|---|
| Right | 1 VM, 2 GND, 3-6 coil pins (unused), 7 logic supply (unused), 8 GND | Rings 1, 2, 8 supported by readings |
| Left | 1 EN, 2-6 unused, 7 STEP, 8 DIR | Confirmed in test 1d |

The adapter's "5V" connector label sits on the manual's NC pin. Treated as unused.

## Test 1b: Continuity on the adapter board (no power)

Set the DMM to Cont. Touch the probe tips together first: it must beep.

| # | Red on | Black on | Expected | Result |
|---|---|---|---|---|
| 1 | Ring 1 (VM) | Ring 2 (VM) | Beep (tied) | OPEN, no beep, confirmed on retest (DMM beeped probe-to-probe). The two VM rings are NOT tied. Which one feeds the board is decided at first power-up. |
| 2 | Ring 2 (VM) | Ring 4 (GND) | No beep | OPEN (pass, no short) |
| 3 | Ring 3 (5V) | Ring 4 (GND) | No beep | OPEN (pass, no short) |
| 4 | Ring 3 (5V) | Ring 2 (VM) | No beep | OPEN (pass, no short) |

Adapter 2: same results as adapter 1 (all four OPEN). No shorts on either adapter. Both kits are built the same way.

## Test 1c: Resistance through the cable (cable plugged in, no power) - UNRESOLVED

Black probe on the GND hole of the OLED board. Red probe on each adapter ring. DMM in 2-wire resistance.

| Right-column ring (top to bottom) | Reading |
|---|---|
| 1 | 24.362 kohm |
| 2 | 0.190 ohm |
| 3 | Overload (open) |
| 4 | Overload (open) |
| 5 | Overload (open) |
| 6 | Overload (open) |
| 7 | Overload (open) |
| 8 | 0.189 ohm |

Result: rings 2 and 8 are ground. Ring 1 has no short to ground (24 kohm). Rings 3-7 are open. This fits the A4988 footprint hypothesis above, not the printed labels. Still to confirm: ring 1 = VM and the left-column EN / STEP / DIR holes, by continuity to the cable contacts. No power until then.

## Test 1d: Adapter holes to the ribbon cable's free-end contacts (no power) - DONE

Ribbon plugged into the adapter only. Free plug contacts numbered 1 to 6 left to right. DMM in 2-wire resistance.

| Red on | Black on | Reading | Meaning |
|---|---|---|---|
| Right ring 1 | Contact 1 | 0.183 ohm | Connected: ring 1 is contact 1 |
| Right ring 1 | Contact 6 | Overload | Not connected |
| Right ring 2 | Contact 3 | 0.179 ohm | Connected: ring 2 (GND) is contact 3 |
| Left ring 1 (EN label) | Contact 4 | Overload | NOT connected. The left-column guess is wrong or incomplete |
| Left ring 7 | Contact 5 | Overload | NOT connected |
| Left ring 8 | Contact 6 | Overload | NOT connected |

The three "Overload" rows above were bad probe contact on the tiny contacts. A full sweep of 13 holes per contact found the real links:

| Cable contact | Signal (manual order) | Adapter hole | Reading |
|---|---|---|---|
| 1 | VM | Right ring 1 | 0.183 ohm |
| 2 | NC (adapter label "5V") | Not tested, unused | n/a |
| 3 | GND | Right ring 2 (ring 8 is also GND) | 0.179 ohm |
| 4 | EN | Left ring 1 | 0.182 ohm |
| 5 | STEP (CLK) | Left ring 7 | 0.175 ohm |
| 6 | DIR | Left ring 8 | 0.166 ohm |

Every other hole read Overload against contacts 4, 5 and 6, so each signal has one hole. This matches the common A4988 driver footprint. Lesson: one Overload can be a bad probe contact; repeat before trusting it.

## Board buttons (found by testing, Oct 26)

Two buttons on the edge opposite the motor plug. The lower one (nearer the ribbon connector) is KEY0: short press scrolls, long press opens the menu / confirms. The upper one is KEY1: scrolls the other way, long press is Return. A short press on the home screen cycles Step Mode, Stop and UART Location. The menu list wraps: About, Home, Sensor, Calibration, and more (as in the manual).

## Planned tests (pending)

| # | Test | Result |
|---|---|---|
| 2 | Power-only at 12 V (1 A limit). Wiring: supply + to right ring 1 (VM), supply - to right ring 2 (GND), EN/STEP/DIR open, motor and ribbon connected | PASS. Supply showed 11.997 V, 0.024 A, 0.298 W in constant-voltage mode. OLED booted to "Step Mode" with Angle 359.51 and a small Error value. Idle current is low (24 mA), so the motor coils are probably not energized yet. Right ring 7 (A4988 logic-supply position) to GND: about 2.5-2.6 V with VM on, about 1.5-1.6 V with VM off. Not a clean 5 V and not 0 V, so that hole is connected to something on the adapter or board. Never linked to a cable contact, so it is unknown whether it is the manual's NC pin. Decision: leave it unconnected on the breadboard and keep the manual's pin 2 (NC) unconnected on the PCB |
| 2b | Encoder calibration from the OLED menu (Calibration, long press KEY0), supply on at 12 V | PASS. Shaft turned slowly by itself, then the screen returned to Step Mode. Angle 359.82, Error flickering about 0.03 to 0.05 degrees (sensor is 14-bit, about 0.022 degrees per count, so this is 1-2 counts of noise). No settings were changed |
| 3a | EN test: jumper from left ring 1 (EN) to right ring 2 (GND), supply at 12 V | Supply current 0.0586 A with EN tied to GND, 0.024 A with EN open. The 34 mA rise (about 0.4 W) means the driver turned on. So EN open = disabled and EN low = enabled: active-low (OLED setting "Normal"), with the pin held high internally when open. The jumper contact was poor (38 to 140 ohm on the DMM) but still a valid logic low. Hum or whine: not reported |
| 3 | Step pulses from the function generator, Dir flip | PASS (Oct 26-27). Generator: square wave, 100 Hz, 0 V low / 3.3 V high, output load High Z, checked on the scope first (top 3.3 V, bottom 0 V). Signal went through a 1X scope probe hook to left ring 7 (STEP), probe ground to the blue rail, EN tied to GND, DIR open. Supply current 0.059 A while stepping, no noise. Angle counted up about 114.8 deg in 10 s (1000 pulses), so about 0.1148 deg per pulse, about 3,136 pulses per turn. That matches 1/16 microstepping: 3,200 pulses per turn, 0.1125 deg per pulse, about 8.9 pulses per degree. Error stayed within -0.11 to +0.07 deg. With DIR (left ring 8) tied to GND the Angle counted down. So DIR open = up, DIR low = down. DIR driven high from a 3.3 V source: not tested separately. Micro Step menu value: not read yet |
| 4 | 100 back-and-forth moves (shaft push test only if we decide it is safe) | pending |
| 5 | Nucleo drives Step/Dir/Enable, measure steps per degree | pending |
| 6 | Load test on the Neewer 12 V adapter with the fuse in line | pending |
| 7 | Laser switch through the MOSFET (220 ohm gate, 10k pulldown) | PASS (Oct 27-28, different lab: Agilent E3631A supply, HP 34401A DMM). Part marked LU024N (IRLU024N, I-PAK). Pins with the text upright and leads down: left Gate, middle Drain (also the metal tab), right Source. Diode test: Source to Drain 0.56 V, reverse OPEN, Gate OPEN both ways. Circuit: 5 V rail to laser red wire (+), laser blue wire (-) to the MOSFET drain, source to ground, gate through 220 ohm to a 3.3 V signal, gate also held to ground by 10 kohm. 3.3 V on the gate: laser on. Gate lead pulled out (10 kohm pulls it low): laser off. Repeated several times. Laser current: 0.025 A at 5 V (about 0.125 W) with the laser on. Bench lesson: the dual banana plug can be inserted rotated 180 degrees, which flipped the rails (red rail read -5 V). With reversed rails the laser lit dimly through the MOSFET's body diode and ignored the gate. Always check rail polarity with the DMM before any power |

## PCB pin table (fills in as tests finish)

| Signal | S42C pin | Voltage | Source on PCB | Result |
|---|---|---|---|---|
| VM | 1 | 12 V (tested 11.997 V; range 12-24 V). Idle 24 mA, enabled 59 mA | Fused 12 V rail | PASS on bench supply. Real load current with the Neewer adapter: pending |
| NC | 2 | none | Leave unconnected | Not used |
| GND | 3 | 0 V | Common ground (shared with the Nucleo and laser) | PASS |
| EN | 4 | 3.3 V logic. Active-low: open = off, GND = on | Nucleo pin | Bench: PASS with a jumper to GND. Nucleo drive: pending |
| STEP | 5 | 3.3 V logic, counts rising edges | Nucleo pin | Bench: PASS at 100 Hz from the generator. Nucleo drive: pending |
| DIR | 6 | 3.3 V logic. Open = up, GND = down | Nucleo pin | Bench: PASS. Nucleo drive: pending |
| Laser + | n/a | 5 V | 5 V line | PASS, 25 mA |
| Laser - | n/a | switched to GND by the MOSFET drain | IRLU024N drain (gate 220 ohm from a Nucleo pin, 10 kohm to GND, source to GND) | PASS |
