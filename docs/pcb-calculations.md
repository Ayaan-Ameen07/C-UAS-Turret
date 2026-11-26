# PCB calculations

My sizing math for the carrier PCB. Inputs come from datasheets (the load test
was skipped on purpose, so I design to the datasheet worst case).
Last updated: Nov 10, 2026.

## 1. Current budget at 12 V

**Why:** this one number sets the fuse, the reverse-guard MOSFET, the trace
widths and the adapter I buy.

| Input | Value | Source |
|---|---|---|
| Motor current (each) | 1.65 A max at 12 V | S42C manual |
| Motors | 2 | |
| 5 V side worst case | 5 A (Pololu D24V50F5 max: Pi, Coral, laser) | Pololu |
| Buck efficiency | 0.9 | Typical |
| Margin | 1.25 | My choice |

Motors:

$$I_{motors} = 2 \times 1.65\ \text{A} = 3.30\ \text{A}$$

Buck output power:

$$P_{out} = 5\ \text{V} \times 5\ \text{A} = 25\ \text{W}$$

Buck input power (the buck keeps the watts, minus about 10% lost as heat):

$$P_{in} = \frac{P_{out}}{\eta} = \frac{25\ \text{W}}{0.9} = 27.8\ \text{W}$$

Buck current at 12 V:

$$I_{buck} = \frac{P_{in}}{V_{in}} = \frac{27.8\ \text{W}}{12\ \text{V}} = 2.32\ \text{A}$$

Total worst case, and with margin:

$$I_{total} = 3.30 + 2.32 = 5.62\ \text{A}$$

$$I_{design} = 1.25 \times 5.62 = 7.0\ \text{A}$$

**Result:** a 5 A adapter is not enough at worst case. I chose a **12 V
adapter rated 8 A or more** (8.33 A / 100 W is a common size). The barrel jack
must also be rated about 8 A or more (many are only 5 A).

## 2. Fuse size

**Why:** a fuse that is too small blows during normal use. A fuse that is
too big never blows, so the jack or a trace burns first.

Low limit (blade fuses should run at 80% of their rating or less):

$$I_{fuse} \ge \frac{5.62\ \text{A}}{0.8} = 7.03\ \text{A}$$

High limit: no bigger than the weakest part in the path (barrel jack,
about 8 A).

$$7.03\ \text{A} \le I_{fuse} \le 8\ \text{A}$$

**Result:** **7.5 A ATC/ATO blade fuse** in a PCB blade holder. This replaces
the old "15 A final" plan, because 15 A is bigger than the jack and would not
protect it.

## 3. Reverse-guard P-MOSFET

**Why:** the MOSFET carries all the current, so its on-resistance, Rds(on),
turns into heat. I want under 0.5 W so a small surface-mount part needs no
heatsink.

$$R_{ds(on)} \le \frac{P_{max}}{I^2} = \frac{0.5\ \text{W}}{(5.62\ \text{A})^2} = 15.8\ \text{m}\Omega$$

| Spec | Requirement | Why |
|---|---|---|
| Rds(on) | 15.8 mOhm or less (at Vgs = -10 V) | Heat under 0.5 W |
| Vds | 30 V or more | 24 V hedge plus spikes |
| Id | 10 A or more | Well above 5.62 A |
| Vgs limit | usually +/-20 V | Checked below |

**Gate clamp:** at 12 V in, the gate sees -12 V (inside +/-20 V). On a 24 V
supply it would see -24 V and die. A **15 V zener** from gate to source caps
it at 15 V, and a **100 kOhm** resistor from gate to GND turns the MOSFET on.
At 12 V the zener does nothing, so the MOSFET still gets the full -12 V.

## 4. TVS diode check (SMCJ15CA)

| Check | SMCJ15CA | Limit | OK? |
|---|---|---|---|
| Stays quiet at 12.5 V | Standoff 15 V | Above 12.5 V | Yes |
| Clamp below the buck limit | 24.4 V max | Pololu max 38 V | Yes |
| Clamp vs motor limit | 24.4 V max | S42C VM 12-24 V | Yes (24.4 V is only at a full 61.5 A surge) |

**Result:** use **SMCJ15CA**, the two-way (bidirectional) version of SMCJ15A with the same 15 V standoff and 24.4 V clamp. I chose it because it works either way round, so it cannot be soldered backwards.


**Update Nov 19 (battery option): use SMCJ18CA instead.** A 4S LiPo reaches
16.8 V full, which is above SMCJ15CA's ~16.7 V breakdown, so the 15 V part
would conduct and overheat. SMCJ18CA (18 V standoff, about 29 V clamp, same
SMC footprint) stays off up to 18 V. Trade-off: in a big spike the clamp is a
little above the S42C's 24 V rating; the Pololu (38 V max) is fine. The 15 V
gate zener still works at 16.8 V: it leaks only about 18 uA through the 100k.

## 5. Bulk capacitor

**Result:** one **1000 uF, 35 V** electrolytic on the +12V rail. 35 V because
spikes can reach the TVS clamp (24.4 V), and 35 V is the next standard rating
above that. 1000 uF is the top of the usual 470-1000 uF range for motor
supplies, since there are two motors.

## 6. Trace widths

IPC-2221 formula, outer layer, 1 oz copper (1.378 mil thick), 10 C rise:

$$I = 0.048\,\Delta T^{0.44}\,A^{0.725}, \qquad w = \frac{A}{t}$$

| Path | Current | Min width | I use |
|---|---|---|---|
| Jack, fuse, MOSFET, +12V main | 7.5 A (fuse rating) | 4.84 mm | 5 mm or a copper zone |
| +12V to each motor | 1.65 A | 0.60 mm | 1 mm |
| +5V to the Pi | 5 A | 2.77 mm | 3 mm |
| STEP, DIR, EN, LASER_CTRL | mA | n/a | 0.25 mm |
| GND | all | n/a | full copper pour on the bottom layer |

Connector check: XH pins (about 3 A each) carry 1.65 A per motor. The Pi gets
5 V on 2 pins and GND on 2 pins, so about 2.5 A per pin at the 5 A worst case.
