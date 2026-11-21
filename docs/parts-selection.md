# C-UAS Turret carrier PCB: parts selection

Branch `pcb-parts`, made from `docs/design-decisions` at 98e0ee4 ("Add PCB schematic: 4 pages, ERC clean").
KiCad 10.0.6. 2-layer, 1 oz, JLCPCB. Worst case 5.62 A at 12 V (7.0 A with margin).
Work done unattended overnight, 2026-11-11 (all times UTC).

## Aru's decisions (Nov 12, 2026) — these override the "Needs Aru" list below

| Item | Decision | Why I chose it |
|---|---|---|
| Q1 reverse-guard P-FET | **Diodes DMP3013SFV-7** (Digi-Key DMP3013SFV-7DICT-ND, $1.00). 9.5 mOhm max at -10 V, Vgs +/-25 V, -30 V. Symbol `Transistor_FET:DMP3013SFV`, footprint `Package_SON:Diodes_PowerDI3333-8`. Swap the symbol in the schematic (same G/D/S wiring). | Everything ships in one Digi-Key cart. Give the drain pads a big copper area. |
| Barrel jack J1 | **Same Sky PJ-063BH** (CP-063BH-ND) on `Connector_BarrelJack:BarrelJack_CUI_PJ-063AH_Horizontal` | Matches KiCad's built-in footprint, 8 A. |
| Pololu D24V50F5 | **Buy 1** (the board holds one) | Grokbot's qty 2 was a default guess. |
| Q2 laser FET | **Buy my own IRLU024N** (the ECE one is a loan I must return) | Can't return a part that is soldered in. |
| 7.5 A fuse | Use my AKOSN kit | Already own it. |
| Pi and laser cables | Pre-crimped JST XH cables (no crimp tool) | XH crimps need a special tool I don't have. |
| Shipping | Ground | The board is not ordered yet, so parts are not needed faster. |
| Status LEDs D3-D5 | **Red**: Kingbright APT2012LSECK/J3-PRV (Digi-Key 754-1935-1-ND), 0805, 1.8 V at 2 mA. Same footprint `LED_SMD:LED_0805_2012Metric`; resistors stay 4.7k / 1.5k / 1.5k (about 2.2 mA each) | I want red LEDs. |
| 12 V adapter | Amazon YOOFONE 12 V 8 A 96 W, 5.5 x 2.5 mm, center positive (ASIN B0DPZXBCJ3, $12.39) | Meets spec at a quarter of the GlobTek price; plug size confirmed on the listing photo. |
| Nucleo CN7 offset / standoff height | No calipers and no Nucleo right now: use the inferred 1.016 mm offset; do a 1:1 paper print fit test when I have the Nucleo, before the JLCPCB order; buy an M3 standoff assortment and pick the height at build time | Paper test needs no tools. |

## Needs Aru (overnight notes)

1. **Q1 part.** Vishay SUD50P04-08-GE3 still has no Digi-Key, Mouser or Arrow stock (Octopart, 2026-11-11 13:37). Only Future has 4,000, sold as 2,000-piece reels.
   - **Infineon IPD50P04P413ATMA2 is now checked against its datasheet** (Infineon IPD50P04P4-13 Rev 1.0, 2011-03-14, read 2026-11-12 13:37 from Farnell's copy because infineon.com served no PDF):
     - Vds -40 V; Vgs ±20 V; Id -50 A at Tc 25 °C (p.1).
     - Rds(on) 9.2 mΩ typ, 12.6 mΩ max at Vgs -10 V, Id -50 A (p.2). That's under your 15.8 mΩ limit. The datasheet gives no -4.5 V value, which you don't need.
     - Vgs(th) -2.0 to -4.0 V (p.2). Your zener and 100 kΩ circuit gives about -12 V, well past that.
     - RthJC 2.6 K/W; RthJA 40 K/W on 6 cm² of copper, or 62 K/W on a minimal footprint (p.2-3).
     - Pins: gate pin 1, drain pin 2 and tab, source pin 3, package PG-TO252-3-313 (p.1). This matches `cuas:SUD50P04-08` (pad G at pin 1, D on the tab, S at pin 3).
     - Loss: 0.40 W at 5.62 A at 12.6 mΩ, and about 0.6 W hot. Give the drain tab about 6 cm² of copper.
   - Stock (Octopart, 2026-11-11 13:37): Mouser 726-IPD50P04P413ATM 9,349 at $1.74; Newark 5,448 cut tape at $1.74; Arrow 1,847 at $1.395. No Digi-Key row.
   - The only Q1 option Digi-Key stocks is Diodes DMP3013SFV-7 (DMP3013SFV-7DICT-ND, 25,059 at $1.00). It needs `Package_SON:Diodes_PowerDI3333-8` and the `Transistor_FET:DMP3013SFV` symbol, which is a schematic edit I did not make.
   - **Recommendation:** make IPD50P04P413ATMA2 the Q1 part on the existing DPAK footprint and buy it from Mouser or Newark. It needs no layout or schematic change.
2. **Barrel jack lead changed.** I made Same Sky PJ-063BH (5.5x2.5, 8 A, 24 V) the lead instead of Tensility 54-00167. Its datasheet drawing (p.2) matches KiCad's built-in `Connector_BarrelJack:BarrelJack_CUI_PJ-063AH_Horizontal` exactly. I could not get Tensility's drawing, so the 54-00167 would need a hand-made footprint built from a drawing I haven't seen. The Tensility part stays as the backup. 24 V is enough for a 12 V rail.
   - **Recommendation:** sign off on PJ-063BH. It's verified against its own drawing, it's in stock at Digi-Key, and it needs no hand-made footprint.
3. **Wrong footprints in the schematic now.** These are leftovers to overwrite when you assign footprints: J1 = QFN-40, F1 = PLCC-84, Q1 = TQFP-44, J6/J7 = speakON. All the others are blank.
4. **Q1/Q2 pad names.** Device:Q_PMOS and Device:Q_NMOS number their pins "G", "D", "S". KiCad's built-in TO-252/TO-251 footprints number pads 1/2/3, so they would not connect. That's why I made `cuas:SUD50P04-08` and `cuas:IRLU024N` with pads named G/D/S. Use those two, and the existing symbols need no change.
5. **Nucleo socket mirror.** KiCad's `PinSocket_2xNN` puts pin 2 at -2.54 mm. A Nucleo plugged in face-up needs pin 2 at +2.54 mm. I made mirrored footprints `cuas:PPPC102LFBN-RC_NucleoZio_2x10` and `cuas:PPPC172LFBN-RC_NucleoZio_2x17`. Do not use the stock PinSocket ones for J8/J9.
6. **CN7 row offset is inferred, not dimensioned.** ST's Figure 6 doesn't dimension CN7 directly. I derived CN7 pin 1 as 1.016 mm (40 mil) below CN11/CN12 pin 1 from the 20.32 mm dimension and the Arduino 160 mil D7/D8 gap; my pixel measurements gave 0.87 to 1.16 mm. Print the board 1:1 and test-fit the Nucleo before ordering.
   - **Recommendation:** check one number on your actual Nucleo with calipers: CN7 pin 1 should sit about 1.0 mm lower (toward Ethernet) than CN12 pin 1 and 7.62 mm inboard of it. If that holds, order. If it's off, tell me the reading and I'll move J8/J9.
7. **Nucleo hole size.** KiCad's Nucleo-144 footprint draws the board's holes at 3.0 mm. M3 screws may be tight in the Nucleo itself. The carrier side uses `MountingHole_3.2mm_M3`, which is fine.
8. **Standoff height.** The PPPC sockets are listed at 8.5 mm tall. Measure how far the Nucleo's Zio male pins stick out of its bottom, then pick standoffs so the board seats fully (about 8.5 mm plus any gap).
9. **Motor connector pitch.** JST XH is 2.50 mm pitch. The S42C ribbon plug measured 12.7 mm across 6 pins, which is 2.54 mm, so it is probably an XH-style clone. Over 6 pins that's 0.2 mm of creep, which usually still mates, but check one plug in a B6B-XH-A before ordering many.
10. **5 A through one Pololu pin.** J3 carries the whole 5 V load through the VOUT pin, and 0.1" header pins are usually rated around 3 A. Solder the module straight into J3 (no socket) and add a short wire from VOUT to the 5 V copper if the Pi draws near 5 A.
11. **Q2 is the ECE loan IRLU024N.** If you buy one: Mouser 942-IRLU024NPBF, 12,811 in stock, $1.83.
12. **Lab adapter plug.** A 5.5x2.1 mm plug is loose in a 2.5 mm jack. Use the 5.5x2.5 Mean Well adapter below.
13. **Stock sources.** Digi-Key's own pages sat behind a Cloudflare human check, which I left alone. Digi-Key numbers came from Octopart's Digi-Key rows. At 06:30 Octopart's search also showed a human check (left alone). After that I read Octopart part pages directly and, where they had no Digi-Key row, used the distributor shown. Every reading below names its source and time.
14. **Mating parts for JST headers.** Order XHP-2, XHP-4 and XHP-6 housings plus SXH-001T-P0.6 crimps, or reuse the S42C cables for the motors.
15. **Mounting holes are not in the schematic.** Place the two `MountingHole:MountingHole_3.2mm_M3` footprints directly in the PCB editor at the positions below. I did not edit the schematic.

## Parts table

Price is unit price at qty 1 unless noted. "n/r" = not read. Lead time: none of the pages I could reach gave a lead time. Every part listed with stock was shown as in stock now.

| Function | Ref / net | MPN | Digi-Key # | Price | Stock (source, time) | Lead time | Footprint (Library:Name) | Datasheet check | Backup MPN |
|---|---|---|---|---|---|---|---|---|---|
| 12 V input jack | J1 / +12V_IN | Same Sky PJ-063BH | CP-063BH-ND | $1.73 | 11,646 (Digi-Key via Octopart, ~06:34) | in stock | Connector_BarrelJack:BarrelJack_CUI_PJ-063AH_Horizontal | Datasheet p.2 PCB layout: pin 1 slot 3.0x1.0 at 12.00 mm from front, pin 2 slot 2.3x1.0 at 6.00, MS slots 1.0x2.5 at 5.00 and 9.00 apart, NPTH 1.6 at 3.00. KiCad pads: 1 at (0,0) drill 3x1, 2 at (0,6) drill 2.3x1, MP at (±4.5,7) drill 1x2.5, NPTH 1.6 at (0,9). Match. Pad 1 = center pin = Barrel_Jack pin 1. | Tensility 54-00167 (839-54-00167-ND, 12,200, $0.65, 05:40) |
| XT60 input (DNP) | J2 | AMASS XT60PW-M | n/r | n/r | not ordered | n/a | Connector_AMASS:AMASS_XT60PW-M_1x02_P7.20mm_Horizontal | Name confirmed in KiCad 10.0.6. Male on the board, female on the source cable. | XT60PW-F (Connector_AMASS:AMASS_XT60PW-F_1x02_P7.20mm_Horizontal) |
| Fuse holder | F1 | Littelfuse 178.6165.0002 | WK6265-ND | $5.72 | 13,448 (Digi-Key via Octopart, 05:42) | in stock | Fuse:FuseHolder_Blade_ATO_Littelfuse_FLR_178.6165 | 30 A, 80 V, PCB through-hole, ATO/ATC blade. KiCad footprint is made for this exact part: 8 pads, drill 1.4 on 2.2 mm pads, side 1 at x 0/3.5, side 2 at x 9.3/12.8, NPTH 2.4 at (6.4,1.25). I could not open Littelfuse's drawing to re-measure it. | Keystone 3557-2 (36-3557-2-ND, 186,343, $1.31, 05:42); no KiCad footprint |
| Fuse 7.5 A | F1 insert | Eaton Bussmann ATC-7-1/2 | n/r | $5.14 | 1,215 (Mouser 504-ATC-7-1/2-2) | in stock | (goes in F1) | 7.5 A, 32 V ATC blade, Production. | Any 7.5 A ATC/ATO from your AKOSN kit (Littelfuse 0257007.5PXPV is obsolete) |
| Reverse-polarity P-FET | Q1 | Infineon IPD50P04P413ATMA2 | none listed | $1.74 | 9,349 (Mouser 726-IPD50P04P413ATM); Newark 5,448; Arrow 1,847 at $1.395 (Octopart, 2026-11-11 13:37) | in stock | cuas:SUD50P04-08 (TO-252, pads G/D/S) | Infineon datasheet Rev 1.0 (Farnell copy): Vds -40 V, Vgs ±20 V, Id -50 A (p.1); Rds(on) 12.6 mΩ max at -10 V (p.2); Vgs(th) -2 to -4 V (p.2); RthJA 40 K/W on 6 cm² (p.2-3). Pin 1 G, 2/tab D, 3 S (p.1). | Vishay SUD50P04-08-GE3, same footprint (8.1 mΩ max, ±20 V, datasheet p.1-2); stock only on Future reels |
| Q1 gate zener | D1 | onsemi MMSZ5245BT1G | MMSZ5245BT1GOSCT-ND | $0.17 | 64,495 (Digi-Key via Octopart, 05:45) | in stock | Diode_SMD:D_SOD-123 | Datasheet p.3: Vz 14.25/15/15.75 V at 8.5 mA, 500 mW, SOD-123, cathode = pin 1 = KiCad pad 1 = D_Zener K. | Diodes MMSZ5245B-7-F (MMSZ5245B-FDICT-ND, 324, $0.21, 05:45) |
| Q1 gate pull-down | R1 | Stackpole RMCF0805FT100K | n/r | ~$0.003 (Avnet reel price) | 40,000 (Avnet, ~06:44) | in stock | Resistor_SMD:R_0805_2012Metric | 100 kΩ 1% 0.125 W 0805. | Yageo RC0805FR-07100KL (Newark 94,627, $0.101) |
| 12 V TVS | D2 | Littelfuse SMCJ15CA | n/r | $0.321 | 1,715 (Arrow via Octopart) | in stock | Diode_SMD:D_SMC | Datasheet p.2: Vrwm 15 V, Vbr 16.7-18.5 V, Vc 24.4 V at 61.5 A, 1500 W, DO-214AB, bidirectional (no polarity). | Vishay SMCJ15CA-E3/57T (Arrow 205, $0.367) |
| 12 V bulk cap | C1 | Panasonic EEU-FR1V102 | n/r | $0.524 (qty 100 price) | 85,244 (Arrow via Octopart) | in stock | Capacitor_THT:CP_Radial_D12.5mm_P5.00mm | 1000 µF 35 V, 12.5x20 mm, 5.0 mm lead pitch, 0.6 mm leads, 2.6 A ripple, 10,000 h. | Nichicon UHE1V102MHD, 12.5x25, P5.0 (Arrow 2,704, $1.06) |
| 12 V LED | D3 / R2 | Kingbright APT2012LZGCK | 3754-1939-1-ND | $0.52 | 73,718 (Digi-Key via Octopart, ~06:34) | in stock | LED_SMD:LED_0805_2012Metric | Datasheet p.2: Vf 2.2/2.65/3.0 V at 2 mA, 525 nm green, 100 mcd typ at 2 mA. (12-2.65)/4.7k = 1.99 mA. Pad 1 = cathode = LED K. | Würth 150080GS75000 (3732-4983-1-ND, 57,310, $0.19) |
| 12 V LED resistor | R2 | Stackpole RMCF0805FT4K70 | n/r | ~$0.003 (Avnet reel price) | 5,000 (Avnet, ~06:44) | in stock | Resistor_SMD:R_0805_2012Metric | 4.7 kΩ 1% 0805. | Any 4.7 kΩ 1% 0805 |
| 5 V regulator | J3 (module) | Pololu D24V50F5 | not at Digi-Key | $32.95 | 245, Rationed/Active (pololu.com, 05:32) | in stock | Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical (solder module straight in) | Pin order from the labeled photo on pololu.com/product/2851: EN, VIN, GND, GND, VOUT. Matches the schematic. | Socket it with Sullins PPTC051LFBN-RC (S6103-ND, 27,363, $0.44, ~06:34) on Connector_PinSocket_2.54mm:PinSocket_1x05_P2.54mm_Vertical. Not advised at 5 A. |
| Pi 5 V ferrite | FB1 | Murata BLM31SN500SZ1L | n/r | $0.293 (qty 5) | 34,629 (Newark via Octopart) | in stock | Inductor_SMD:L_1206_3216Metric | 50 Ω at 100 MHz, 10 A rated (12 A max), 1.6 mΩ DC, 1206. | Murata BLM31SN500SH1L (same ratings) |
| Pi 5 V TVS | D6 | Littelfuse SMAJ5.0CA | n/r | $0.514 | 5,700 (Newark via Octopart) | in stock | Diode_SMD:D_SMA | Datasheet p.2: Vrwm 5.0 V, Vbr 6.4-7.0 V, Vc 9.2 V at 43.5 A, 400 W, DO-214AC, bidirectional. | Bourns SMAJ5.0CA |
| 5 V bulk cap | C2 | Panasonic EEU-FR1C101 | n/r | $0.398 | 8,986 (Newark via Octopart) | in stock | Capacitor_THT:CP_Radial_D5.0mm_P2.00mm | 100 µF 16 V, 5x11 mm, 2.0 mm pitch, 0.5 mm leads. | Not settled: no listing found for Nichicon UHE1C101MED, UPW1C101MDD or UHE1C101MDD. Any 100 µF ≥16 V, 5 mm dia, 2.0 mm pitch radial fits. |
| 5 V decoupling | C3 | Samsung CL21B104KBCNNNC | n/r | $0.009 (Arrow, min 8,000) | Arrow | in stock | Capacitor_SMD:C_0805_2012Metric | 100 nF 50 V X7R 0805. | Yageo CC0805KRX7R9BB104 (no listing found) |
| 5 V LED | D4 / R3 | Kingbright APT2012LZGCK | 3754-1939-1-ND | $0.52 | as D3 | in stock | LED_SMD:LED_0805_2012Metric | (5-2.65)/1.5k = 1.57 mA, still bright for this LED (rated at 2 mA). | Würth 150080GS75000 |
| Laser-on LED | D5 / R4 | Kingbright APT2012LZGCK | 3754-1939-1-ND | $0.52 | as D3 | in stock | LED_SMD:LED_0805_2012Metric | Same as D4. | Würth 150080GS75000 |
| LED resistors 1.5 k | R3, R4 | Stackpole RMCF0805FT1K50 | n/r | ~$0.002 (Avnet reel price) | 135,000 (Avnet, ~06:44) | in stock | Resistor_SMD:R_0805_2012Metric | 1.5 kΩ 1% 0805. | Any 1.5 kΩ 1% 0805 |
| Laser switch | Q2 | Infineon IRLU024NPBF | n/r | $1.83 | 12,811 (Mouser 942-IRLU024NPBF) | in stock; ECE loan | cuas:IRLU024N (TO-251 vertical, pads G/D/S) | Datasheet (irlr024npbf.pdf) p.2-3: 55 V, Rds(on) 65 mΩ at 10 V, 80 mΩ at 5 V, 110 mΩ at 4 V, Vgs(th) 1-2 V, Id 17 A. I-Pak G-D-S (standard; the text doesn't state it, so check the part's markings). 2.29 mm pitch, 1.1 mm drill. | IRLR024N (DPAK version), needs a DPAK G/D/S footprint |
| Q2 gate resistor | R5 | Stackpole RMCF0805FT220R | n/r | $0.005 | 2,925 (Arrow, ~06:44) | in stock | Resistor_SMD:R_0805_2012Metric | 220 Ω 1% 0805. | Any 220 Ω 1% 0805 |
| Q2 gate pull-down | R6 | Stackpole RMCF0805FT10K0 | n/r | n/r | 1,535,000 (Arrow, ~06:44) | in stock | Resistor_SMD:R_0805_2012Metric | 10 kΩ 1% 0805. | Any 10 kΩ 1% 0805 |
| Pi power | J4 | JST B4B-XH-A | n/r | $0.098 | 6,907 (Heilind via Octopart) | in stock | Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical | JST eXH.pdf: 2.50 mm pitch, 3 A per contact at AWG 22. Pins 1-2 5V_PI, 3-4 GND gives 6 A total across two contacts. | Mate: XHP-4 (Arrow 790,455, $0.097) + SXH-001T-P0.6 (Heilind 270,000, $0.023) |
| Laser | J5 | JST B2B-XH-A | n/r | $0.057 | 714,390 (Heilind via Octopart) | in stock | Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical | As J4. | Mate: XHP-2 (no Octopart listing found) |
| Motor 1, Motor 2 | J6, J7 | JST B6B-XH-A | n/r | $0.140 | 6,342 (Heilind via Octopart) | in stock | Connector_JST:JST_XH_B6B-XH-A_1x06_P2.50mm_Vertical | As J4. Pin 1 VM, 2 NC, 3 GND, 4 EN, 5 STEP, 6 DIR. See Needs Aru 9 on pitch. | Mate: the S42C cable or XHP-6 |
| Nucleo CN7 socket | J8 | Sullins PPPC102LFBN-RC | S6106-ND | $1.24 | 30,369 (Digi-Key via Octopart, ~06:34) | in stock | cuas:PPPC102LFBN-RC_NucleoZio_2x10 | 2x10, 2.54 mm, 3 A, 8.5 mm insulator. Footprint mirrored so pin 2 is at +2.54 mm (see Needs Aru 5). | Samtec SSW-110-01-T-D (Newark, 6.9 A) |
| Nucleo CN10 socket | J9 | Sullins PPPC172LFBN-RC | S7120-ND | $2.10 | 3,837 (Digi-Key via Octopart, ~06:34) | in stock | cuas:PPPC172LFBN-RC_NucleoZio_2x17 | 2x17, otherwise as J8. | Samtec SSW-117-01-T-D (Newark, 6.9 A) |
| Nucleo standoff holes (2) | H1, H2 (PCB only) | M3 standoffs, height per Needs Aru 8 | n/a | n/a | n/a | n/a | MountingHole:MountingHole_3.2mm_M3 | Positions below. | n/a |
| Test points | TP1-TP8 | bare pad, no part | n/a | $0 | n/a | n/a | TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm | 2.0 mm pad with 1.0 mm hole: a DMM probe tip sits in the hole. | TestPoint:TestPoint_Pad_D2.0mm (SMD) |
| 12 V adapter | off-board | Mean Well GST120A12-P1M | n/r | n/r | no listing found on Octopart | n/r | n/a | 12 V, 8.5 A, 102 W. Suffix P1M = 5.5x2.5 mm plug, center positive. IEC C14 inlet, so it needs a C13 mains cord. | A 12 V ≥8 A 5.5x2.5 center-positive brick from Amazon. Check the plug is 2.5 mm, not 2.1 mm. |

### Why I chose each part

- **J1 PJ-063BH:** 8 A with a 2.5 mm pin. Its PCB layout matches a footprint that ships with KiCad, so there's nothing hand-made to get wrong.
- **J2 XT60PW-M:** your spec. It's the KiCad-library part, left unpopulated.
- **F1 Littelfuse 178.6165.0002:** rated 30 A, so a 7.5 A fuse is never near its limit, and KiCad has a footprint made for exactly this holder.
- **Fuse ATC-7-1/2:** a current-production 7.5 A blade. Any 7.5 A ATC/ATO from your kit works too.
- **Q1 IPD50P04P413ATMA2:** 12.6 mΩ max meets your 15.8 mΩ limit. It's AEC-Q101, rated for 175 °C, and actually in stock. At 5.62 A it loses about 0.4 W, and a DPAK tab on 6 cm² of copper sheds that. The Vishay SUD50P04-08 has lower resistance but you can only buy it by the reel.
- **D1 MMSZ5245BT1G:** the standard 15 V SOD-123 zener, from a big stock.
- **D2 SMCJ15CA:** 15 V standoff sits just above the 12 V rail, and 1500 W absorbs hot-plug spikes.
- **C1 EEU-FR1V102:** low ESR, 2.6 A ripple, and 35 V gives margin on 12 V.
- **LEDs APT2012LZGCK:** specified at 2 mA (most green 0805s are specified at 20 mA). At 2 mA it gives 100 mcd, which is plenty of brightness.
- **FB1 BLM31SN500SZ1L:** 10 A rated with 1.6 mΩ DC resistance, so at 5 A it drops about 8 mV and wastes about 40 mW.
- **D6 SMAJ5.0CA:** 5.0 V standoff and doesn't start conducting until 6.4 V, so it stays quiet on the 5 V rail and clamps spikes.
- **C2 EEU-FR1C101:** same FR family as C1. It's small and has low ESR.
- **Resistors, Stackpole RMCF0805FT:** a common 1% 0805 line, all values from one family.
- **Q2 IRLU024N:** your loaned part. It's fully on at 3.3 V gate drive (Vgs(th) is at most 2 V).
- **JST XH:** your spec. All four headers are the KiCad-library parts.
- **Sullins PPPC sockets:** big Digi-Key stock and 3 A contacts, enough for logic signals and GND.

## Pololu D24V50F5 pin order

From the labeled photo on pololu.com/product/2851 (read 05:32), left to right: **1 EN, 2 VIN, 3 GND, 4 GND, 5 VOUT**. This matches the schematic, so no labels need swapping.

## Nucleo-144 (NUCLEO-F767ZI) socket and standoff positions

Sources:
- ST UM1974 Rev 11, Figure 6 (p.15), dimensions 48.26, 15.24, 50.80, 2.56, 3.70, 6.24, 16.51, 20.32 and 133.34 mm.
- KiCad 10.0.6 `Module:ST_Morpho_Connector_144_STLink_MountingHoles`. Its five holes agree with Figure 6 to within 0.1 mm.

How to read the numbers:
- Directions are as in Figure 6 seen from the top: ST-LINK at the top, Ethernet at the bottom, CN12 on the right.
- KiCad X increases to the right and Y increases downward (toward Ethernet).
- **Reference point: CN7 pin 1.**

| Feature | X (mm) | Y (mm) | Notes |
|---|---|---|---|
| CN7 (J8) pin 1 | 0.000 | 0.000 | square pad, column away from the CN12 edge |
| CN7 pin 2 | +2.540 | 0.000 | Arduino column (D15...D8 on even pins) |
| CN7 pin 20 | +2.540 | +22.860 | |
| CN10 (J9) pin 1 | 0.000 | +26.924 | same columns as CN7 |
| CN10 pin 34 | +2.540 | +67.564 | |
| Standoff A, free side, ST-LINK end | -45.720 | -4.826 | Nucleo hole (KiCad), X confirmed by Figure 6's 48.26 |
| Standoff B, free side, Ethernet end | -44.450 | +71.374 | Nucleo hole (KiCad), Y confirmed by Figure 6's 16.51 |

The same points measured from Morpho CN11 pin 1, if you want to cross-check against the KiCad Nucleo footprint:
- CN7 pin 1 at (53.340, 1.016).
- CN10 pin 1 at (53.340, 27.940).
- Standoff A at (7.620, -3.810).
- Standoff B at (8.890, 72.390).
- Other Nucleo holes (not used): (55.88, -2.54), (40.64, 48.26), (54.60, 72.39).

How I checked it:
- CN7 and CN10 sit 3 × 2.54 mm inside CN12.
- CN10's last row is 20.32 mm above CN11's last row (88.90 mm), so its pin 1 is at 27.94 mm.
- CN7 pin 1's 1.016 mm Y offset is the inferred value (Needs Aru 6).

Place J8 and J9 at rotation 0° with the footprints from `cuas.pretty`.

## Cost

These are single-board, qty-1 prices, read overnight from the sources named in the table. They are not a quote.

| Group | Parts | Cost |
|---|---|---|
| Digi-Key (via Octopart's Digi-Key rows) | J1 1.73, F1 5.72, D1 0.17, D3-D5 3 × 0.52, J8 1.24, J9 2.10 | **$12.52** |
| Other distributors | ATC-7-1/2 5.14, Q1 (IPD50P04P413ATMA2) 1.74, D2 0.321, D6 0.514, C1 0.524, C2 0.398, FB1 0.293, J4 0.098, J5 0.057, J6-J7 2 × 0.140 | **$9.37** |
| Pololu | D24V50F5 | $32.95 |
| Not counted | R1-R6 and C3 (reel prices only, roughly $0.10 each at qty 1 if you buy cut tape), Q2 (loan), J2 (DNP), XH mating housings and crimps, adapter, standoffs, PCB | |

Board parts total, excluding the Pololu module: about **$21.89**. Including the module: about **$54.84**. Of that, Digi-Key itself is $12.52. If you buy everything at Digi-Key, the other-distributor parts have Digi-Key equivalents I couldn't price behind its human check.

## Library files on this branch

- `pcb/lib/cuas.pretty/SUD50P04-08.kicad_mod`: KiCad TO-252-2 with pads renamed G/D/S. 3D model `pcb/lib/3dmodels/SUD50P04-08.step`.
- `pcb/lib/cuas.pretty/IRLU024N.kicad_mod`: KiCad TO-251-3_Vertical with pads renamed G/D/S (G is the square pad). 3D model `IRLU024N.step`.
- `pcb/lib/cuas.pretty/PPPC102LFBN-RC_NucleoZio_2x10.kicad_mod` and `PPPC172LFBN-RC_NucleoZio_2x17.kicad_mod`: KiCad PinSocket_2x10/2x17 mirrored in X. 3D models `PPPC102LFBN-RC.step` and `PPPC172LFBN-RC.step` (KiCad socket models rotated 180° and shifted to fit).
- All 3D models are from KiCad's own packages3D library (CC-BY-SA 4.0 with exception). Built-in footprints use KiCad's built-in 3D models automatically.
- No `cuas.kicad_sym` was needed. Every part uses the symbol already in the schematic.
- No hand-made footprints were needed. Every footprint is KiCad's own or a direct edit of one.

## Morning steps for Aru

1. Pull the branch: `git fetch origin pcb-parts && git checkout pcb-parts`.
2. In KiCad: Preferences > Manage Footprint Libraries > Project Specific tab. Add a library with nickname `cuas` and path `${KIPRJMOD}/lib/cuas.pretty`.
3. Open the schematic and run Tools > Assign Footprints. Set each ref to the Footprint column of the table above:
   - J1 Connector_BarrelJack:BarrelJack_CUI_PJ-063AH_Horizontal
   - J2 Connector_AMASS:AMASS_XT60PW-M_1x02_P7.20mm_Horizontal
   - F1 Fuse:FuseHolder_Blade_ATO_Littelfuse_FLR_178.6165
   - Q1 cuas:SUD50P04-08
   - Q2 cuas:IRLU024N
   - D1 Diode_SMD:D_SOD-123
   - D2 Diode_SMD:D_SMC
   - D6 Diode_SMD:D_SMA
   - D3, D4, D5 LED_SMD:LED_0805_2012Metric
   - R1-R6 Resistor_SMD:R_0805_2012Metric
   - C1 Capacitor_THT:CP_Radial_D12.5mm_P5.00mm
   - C2 Capacitor_THT:CP_Radial_D5.0mm_P2.00mm
   - C3 Capacitor_SMD:C_0805_2012Metric
   - FB1 Inductor_SMD:L_1206_3216Metric
   - J3 Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical
   - J4 Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical
   - J5 Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical
   - J6, J7 Connector_JST:JST_XH_B6B-XH-A_1x06_P2.50mm_Vertical
   - J8 cuas:PPPC102LFBN-RC_NucleoZio_2x10
   - J9 cuas:PPPC172LFBN-RC_NucleoZio_2x17
   - TP1-TP8 TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm
4. Update PCB from Schematic. Place J8 and J9 at 0° using the Nucleo table, then add two `MountingHole:MountingHole_3.2mm_M3` footprints at standoffs A and B.
5. Before ordering, work through Needs Aru 1, 6 and 9.
