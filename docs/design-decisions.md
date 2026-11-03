# Design Decisions (plain-language version)

Last updated: Oct 30, 2026

The block diagram and a parts directory are in `pcb-flowchart.md`.

This file explains **what we decided, why, and what is still open**.
It is written so someone who has never built a robot can follow it.
It adds to `project-reqs.md` and, where they differ, it is newer.
(Example: `project-reqs.md` says the PCB talks to the Pi over "serial/I2C".
We have now picked one USB cable from the Pi to the Nucleo, which carries power
and serial together. See Decision 2.)

The parts list with links, prices, and "decide by / order by" dates lives in the
BOM spreadsheet (`turret_bom.xlsx`). This file is the reasoning behind it.

---

## The big picture in one paragraph

The turret has two "brains".

- **Brain 1: the Raspberry Pi 5.** It looks through the camera, runs our
  self-trained AI model to answer "is there a drone and where?",
  and decides when the target is locked.
- **Brain 2: the STM32 chip on our custom PCB.** It does exactly what the Pi
  tells it: send the right pulses to the two motors, and switch the laser.

Why two brains? The Pi runs a full operating system (like a tiny laptop), so it
can't promise exact timing. Motors need exact timing or they stutter. The STM32
only does simple jobs, so it can be exact. The Pi does the thinking, the STM32
does the moving.

```
 Camera --> [ Raspberry Pi 5 ] --USB cable--> [ STM32 Nucleo on custom PCB ] --> 2 motor kits
 (USB)       runs the AI model                exact motor timing                + laser
             decides "lock on"
```

**Chip vs board (a common mix-up):** the STM32 is the *chip*. The **Nucleo** is
that chip already mounted on a small ready-made board. Our custom PCB is a
**carrier board**: the Nucleo plugs into it, and its copper traces connect the
Nucleo to the motors, laser, power and Pi. So the same Nucleo we use in
Prototype 1 stays in the finished turret.

---

## Decision 1: The motor brain is an STM32 on a Nucleo (not an ESP32)

**Updated Oct 29:** Prototype 1 runs on the **Nucleo-144 STM32F746ZG** that I
borrowed from the Purdue ECE shop (a loan: it goes back). The **NUCLEO-G474RE**
below is now only an optional buy, in case the shop wants its board back before
Dec 12. The code is Arduino-style or ST's own tools, so it carries over between
the two. The carrier PCB is designed so a Nucleo plugs in (see Decision 13).
I dropped the Oct 26 ESP32 fallback date (I said not to track it).

**Why I chose to use the loan board:** it was already in my hands and free, and
the G474RE was only a hedge against an out-of-stock board. Using what I have lets
me start on the code now.

**What (original plan):** STM32G474. For Prototype 1 we planned the
**Nucleo-G474RE** dev board (a ready-made board with the chip plus a USB
programmer built in, about $20 at Digi-Key).

**Updated Oct 17: carrier-board PCB.** The final custom PCB is a **carrier
board that the Nucleo plugs into** (decided Oct 17), not a board with the bare
chip soldered on. The PCB still carries the real design work (connectors, power
input, fuse, surge diode, laser MOSFET, 5 V module socket, motor connectors),
and there is still soldering. The chip stays on the Nucleo, which is already
known to work. That removes fine-pitch chip soldering, chip start-up problems and
the extra programming header. The bare STM32G474RET6 (64-pin, about $10.70) and
a chip-down board remain in the BOM as an **optional, not-counted** upgrade.

**Resume wording:** say "custom carrier PCB for an STM32 Nucleo". Do not claim
I designed my own microcontroller board.

**Pi link (decided Oct 30): one USB cable.** The Pi talks to the Nucleo over one
USB cable into its programmer port (it shows up as a serial port). The same
cable powers the Nucleo. There are no separate TX/RX/GND wires. See Decision 2.

**One power rule:** the Nucleo and the carrier board must never both power the
same pin. Decided Oct 30: the Nucleo gets power only from the Pi's USB cable, so
the carrier board does not power it.

**Chip-down PCB dropped (Oct 30):** putting the bare STM32 chip on my PCB in
place of the Nucleo would cost about 8-15 more hours and fine-pitch soldering,
and it will not fit before Nov 1. The carrier board stays.

**Why I chose to drop it:** I do not want 8-15 more hours of fine-pitch
soldering. The carrier board still has real design work in it.

**Heads-up on the loan:** the loaned board is a Nucleo-144. The optional
NUCLEO-G474RE in the BOM is a smaller Nucleo-64, so it will not plug into
sockets made for the 144. If the shop wants the loan back before Dec 12, I need
another 144-size board. To check in ST's documents.

**Changed from the earlier plan:** this doc used to say STM32G431 / Nucleo-G431RB.
That board is out of stock with a 99-week lead time, so we moved to the G474 in
the same family. Code and pin choices carry over.

**Why STM32:**
- STM32 chips are what real robots, drones and motor products use. "Custom PCB
  built around an STM32" is a stronger resume line than ESP32.
- The G4 family has precise built-in timers, which is exactly what makes motor
  pulses accurate.

**The catch (honest):** STM32 is harder to learn than ESP32.
To keep it fast, we write code in the simple **Arduino style** (using
PlatformIO in VS Code). That adds roughly 5-6 hours compared with an ESP32,
instead of 10-15 hours with ST's own tools.

**Escape hatch:** if the Nucleo is not driving a motor by **Oct 26**, we switch
to an ESP32-S3. Nothing else in the design changes.

**Why I chose STM32 over ESP32:**
- I asked for whichever one the industry and resume people will like better.
- My main limit is time: 10-12 hours a week, on top of classes and an
  internship. I did not want to spend an insane amount of time troubleshooting,
  and I said that if STM32 cost me only about 5 extra hours, I would take it.
  That is why the code is written Arduino-style.
- I asked how much more STM32 costs than ESP32 and whether employers actually
  care. The answer: a little more money, a steeper learning curve, and yes,
  STM32 reads as more serious for robotics and motor work.
- I wanted a hard fallback, so we set the Oct 26 deadline: if no motor is moving
  by then, I switch to the ESP32-S3.

**Why I chose the carrier-board PCB:** I wanted to lower the risk and time cost
of soldering and starting up a bare chip, while still doing a custom PCB with
real soldering. I asked why I could not just use the Nucleo as the whole
controller, was told I could, and decided to make the Nucleo part of my custom
board. I made the bare chip optional for now.

---

## Decision 2: The Pi and the Nucleo talk over one USB cable

**Updated Oct 30.** This used to say UART (TX, RX, GND wires at 3.3 V). It is now
**one USB cable** from the Pi into the Nucleo's programmer USB port. The cable
carries serial data and also powers the Nucleo.

**Why:** The Pi only sends tiny messages like "aim here" or "fire". A USB serial
port is enough, and it is easy to debug with a laptop. One cable gives power and
data, so the PCB needs no extra serial wires and no second power path for the
Nucleo.

**In Prototype 1** the laptop plays the Pi's role with the same USB cable, so
nothing changes when the Pi takes over.

**Alternatives we rejected:** UART wires (works, but needs wires and a separate
power path), I2C (motor electrical noise can corrupt it), SPI (overkill).

**To verify:** the Pi 5 may limit its USB ports to about 600 mA total unless told
its supply is strong (`usb_max_current_enable=1` in `config.txt`). The Arducam
plus the Nucleo may be near that. Check on the real Pi.

**Why I chose USB over UART:** I wanted the simplest connection that works and is
easy to debug. USB means one cable for power and data, and it matches Prototype 1.
I was also confused at first about what the Pi does versus the laptop, which is
why this doc explains training vs running.

---

## Decision 3: The motors run on 12 V, with a 24 V hedge

**What:** 12 volt supply for the motors.

**Why:**
- A 12 V battery is made of 3 cells and is cheap. A 24 V battery needs 6 cells
  (or an extra boost circuit), roughly $40-70 more overall (estimate).
- A turret is light and slow. 12 V is plenty. The cost of 12 V is a lower top
  speed, which this project will not need.

**The 24 V hedge (agreed Oct 16):**
1. The PCB is built with parts that can handle 24 V (capacitors, fuse,
   connectors, traces), which costs almost nothing extra.
2. We run at 12 V now.
3. If the turret feels slow in P2, upgrading means swapping the battery and one
   small protection diode (SMCJ15A -> a 24 V-class one). No new board.

**What "closed-loop" means:** a normal stepper motor moves N steps and *assumes*
it got there. If it is bumped, it loses its place without knowing. A
closed-loop stepper has a small position sensor (an encoder) so the driver can
check and fix its position. Same motor, plus feedback.

**Why I chose 12 V with a 24 V hedge:**
- I first asked how much slower 12 V is than 24 V, and said that if it is not
  that bad, I would go with 12 V. I also asked for a real number for the extra
  cost of 24 V (the battery needs twice the cells, roughly $40-70 more).
- Then I worried that a turret has to turn the camera fast to track a moving
  target. I liked the idea of drivers that work on both 12 V and 24 V: run 12 V
  now, and keep the option of 24 V without a new board.
- Budget was also a factor: I cannot spend $300 in one month.

---

## Decision 4: The motors are BIGTREETECH S42C closed-loop kits (decided Oct 17)

**What:** Two **BIGTREETECH S42C V1.1** kits (one for pan, one for tilt),
$39.99 each on Amazon. Each kit is the motor plus its driver and position
sensor in one unit, so there is nothing to match up. The STM32 only sends simple
step and direction pulses.

**Why:** we want closed-loop (backlash was named as a top failure risk), and
this is the cheapest hobby-grade closed-loop kit that arrives in time. Plain steppers plus separate drivers (about $50 for two axes) stay in the
BOM only as a not-counted alternative; they are open-loop, which breaks the spec.

**Bring-up results (Oct 25-28, measured on the bench):** both kits power up and
calibrate. Full details and the pin table are in `s42c-bringup-tests.md`.

| Fact | Measured / confirmed |
|---|---|
| Motor power (VM) | 12 V. Vendor page says 12-24 V. 24 mA idle, about 59 mA enabled and stepping with no load |
| Enable (EN) | Active-low. Open = motor off, tied to GND = motor on. Open means "off" is a good fail-safe |
| Step (STEP) | One step per rising edge, 3.3 V logic works. 100 Hz tested |
| Direction (DIR) | Open = one way, tied to GND = the other way |
| Microstep | Default 1/16: about 3,136 pulses per turn measured (3,200 expected), about 8.9 pulses per degree |
| 6-pin control plug | Pin 1 VM, 2 NC (leave open), 3 GND, 4 EN, 5 STEP, 6 DIR |
| Laser switch | IRLU024N, gate through 220 ohm, 10 kohm pulldown, laser draws 25 mA at 5 V. 3.3 V gate = on |

**Still to measure:** both motors' current under load on the real 12 V adapter,
100 back-and-forth moves, and the Nucleo driving STEP/DIR/EN.

**Caution from the manual:** "do not turn the motor by hand after power on".

**Honest unknowns (older notes, now mostly answered):**
- Some reviewers report dead units. Amazon returns are free for 30 days; both of
  my kits worked.

**Why I chose these motors:**
- Closed-loop was in the original spec because backlash (slop) and lost steps
  were identified as a top failure risk for a fast-tracking turret.
- I want to start building as soon as possible: choose motors now so I can start
  the CAD for the shell and camera mount, the breadboard wiring, and model
  training.
- I did not fully trust the first source, so I want each part checked one by
  one, with listings I find myself.
- I wanted every part as its own line with its own link, nothing bundled.

---

## Decision 5: The PCB powers the Pi

**What:** The final PCB takes power in, and splits it into two paths:
1. Motors (12 V), protected by a fuse and a surge-protector diode.
2. The Pi, through a **ready-made 5 V converter module** (plugged into a socket
   on the PCB, so we don't design a regulator from scratch). It must supply
   5 V at about 5 A.

**Why:** one power input and one switch. That is cleaner and what a real
product looks like. It also matches the original plan that the PCB handles
"power distribution".

**Because the PCB order only happens once** (target Oct 30, hard limit Nov 1, because exams start Nov 2), this
power path has to be in the first design.

**Safety net:** the PCB is brand new, so in Prototype 2 the Pi runs from its
own official wall power supply (about $12) first. We switch to PCB power only
after we test the board and trust it.

**Noise note:** motors create electrical noise that can reset a Pi. The Pi's
5 V path gets its own capacitors and short, thick traces to keep it clean.

**Updated Oct 29: one 12 V input feeds everything ("Option 1").** There is a
single power input. 12 V goes to the motors, and a buck converter (a switching
step-down module) makes 5 V for the Pi. The laser uses a small 5 V line from the
same converter. The other two ideas were: Option 2, the Pi on its own wall
supply (works, but two cables and less "one product"), and Option 3, designing my
own converter chip circuit (6-12 extra hours, not for this deadline). Parts that
protect and clean the power are in Decision 12.

**Why I chose Option 1:** I want one supply and some real power filtering so I
learn it, and it reads best on a resume. Option 3 would eat time I need for the
AI model and the CAD.

**Still open: which 5 V module.** Option A is the Pololu D24V50F5 ($32.95, known
good). Option B is a generic AliExpress 5 V / 5 A board ($5.24, unproven, and the
"5 A" claim is doubtful). The two have different sizes, so this must be decided
before the PCB layout is final. I lean toward A (it is the one I can trust to run
the Pi), but I have not confirmed it yet.

**Option C checked Oct 30 (Amazon, sealed USB-C module, $8.99, 8-32 V in, "5 A").**
It is a potted block with a USB-C output and no pins, so it cannot sit on the
PCB. Reviews are mixed on whether it really delivers 5 A, and one says it is not
suitable for a Pi 5. It would also need the `usb_max_current_enable=1` setting.
Not a fit for a module that plugs into the board. Look for a bare module with pins
or screw terminals, input range up to 24 V or more, and 5 A continuous.

**Option D checked Oct 30 (Amazon, BINZET potted block with wire leads, 8-40 V in,
5 V 5 A, about $9.78).** It has wires, not pins, so on the PCB it would go through
screw terminals instead of a socket. The 5 A version shows delivery Nov 18 - Dec 13,
which is too late for the order. The 10 A version (about $9.98) shows Oct 31.
Reviews are mostly good, with a few saying it gives less current than rated.
A possible backup, not a first choice. A screw-terminal footprint on the PCB would
let me swap any module in later.

**Pi, camera and Nucleo (Oct 30):** the 5 V rail feeds the Pi (and the laser). The
Pi powers the Arducam and the Nucleo over USB. The Nucleo is not on the 5 V rail.

**Why I chose to have the PCB power the Pi:** I asked which option is more
time-efficient and looks cleaner and more professional. I also pointed out that
Prototype 2 needs the PCB anyway, and that I want it as early as possible. The
wall-supply safety net in Prototype 2 came from the same thinking: a bug in a
brand-new board should not ruin the checkpoint.

---

## Decision 6: Power input connector on the PCB (decided Oct 17)

**Updated Oct 30: the barrel jack is the main input.** My power source is a wall
plug, so the board has a barrel jack. The XT60 footprint stays on the board but
is **not populated** (empty pads) until a battery is built. A PCB-mount barrel jack
needs to be bought (a few dollars). Match it to my adapter's plug size and
polarity, and pick one rated for at least 5 A.

**Why I chose the barrel jack:** my 12 V source is just a wall plug, and I want it
to work like a USB charger: plug in and everything powers. The XT60 is a battery
connector.

**A battery needs more than an XT60 (to handle later):**
- A battery pack with its own protection board (over/under voltage, over current).
- A way to charge it, away from the turret.
- Only one source connected at a time, with a label (or a power-switching part).
- Voltage range: a 3-cell Li-ion pack sags below 12 V, and the S42C is rated 12-24 V.
  A 4-cell pack (about 12-16.8 V) fits the motors, but then the SMCJ15A TVS would
  be too low. It would need a higher-voltage TVS. To check before building a pack.

**What (Oct 17 plan):** **Option D**: a barrel jack *and* an XT60 battery connector footprint
on the same board. Only one is connected at a time.

**Why:**
- Today the wall adapter plugs into the barrel jack. It cannot be plugged in
  backwards.
- Later a battery drops into the XT60 (the standard drone battery plug, built
  for high current, also hard to reverse), with no board redesign.
- The extra cost is only a few dollars and a little board space.

**Rejected:** a bare screw terminal alone. It is cheap, but it can be wired
**backwards**, which can kill the chip and drivers, and the wires can work loose
from vibration on a moving turret. Barrel jack alone does not suit a battery.

**Rules:**
- Never connect both at once. A label on the board says which one is live.
- The fuse sits right at the power entry, before anything else.
- Optional: a small reverse-polarity protection part as a cheap safety net.

**Why I chose option D:** I asked for the pros and cons of the connector
choices, then picked D. A barrel jack and an XT60 footprint on the same board
means the wall adapter works today, a battery works later, and neither can be
plugged in backwards. The board is ordered once, so power entry has to be right
the first time.

---

## Decision 7: Power plan by prototype (cost control)

The budget is tight, so we buy only what each prototype needs.

| When | Power parts | Notes |
|---|---|---|
| **P1** (now) | 12 V 5 A wall adapter, barrel-jack to screw-terminal adapter, 15 A fuse and holder, SMCJ15A surge diode, 1000 uF capacitor | Check the Purdue ECE shop first; it may have the adapter, jack, fuse parts and capacitor for free |
| **P2** | Pi's 27 W wall power supply | The Pi runs on its own wall supply until the PCB is trusted |
| **P3** | PCB power path (5 V module). Battery only if built. | Battery is optional (see below) |

Notes:
- **Fuse parts:** skip the online store (Hemlock) because of shipping. Buy a
  regular-size ATC inline holder (rated 15 A or more, thick wire) and 15 A ATC
  fuses at an auto parts store, or ask the ECE shop.
- **No fire box.** We dropped the $80 box as overkill.
- **Battery is optional and not counted** in the totals. If built later, it is
  a protected 3-in-series, 2-in-parallel pack (about 11.1 V). Charge only while
  awake and in the room, on a tile or metal tray, never overnight, never use a
  dented or puffy cell. Buy vs build is decided in late November.
- The turret should draw about 45 W on average and about 87 W at peak (a
  deliberately cautious guess).

**Why I chose this power plan:**
- I asked: "Can we just power this with a simple laptop charger for now and do
  battery later?" The battery set was expensive and I cannot spend $300 in one
  month.
- I asked why I need a fire box and rejected it as overkill. Charging rules
  replace it.
- I chose to leave the battery out for now and add it as an optional item once I
  am committed to the project.
- I asked what a fuse is and why it is needed, and chose to skip the online
  store for the fuse parts because of shipping, buying locally or from the ECE
  shop instead.
- I plan to check the Purdue ECE shop on Monday for free parts before ordering.

---

## Decision 8: Raspberry Pi 5 8 GB, bought at P2; Coral waits

**What:** Raspberry Pi 5, **8 GB** (decided Oct 16). The RAM can't be upgraded
later. We do **not** buy the Pi now (decided Oct 17): the Pi, power supply and
cooler are P2 purchases, ordered by Nov 10.

**Training vs running (the thing that confused us):**
- **Training** = teaching the model with thousands of pictures. Heavy work. Done
  once on a laptop or free Google Colab.
- **Running** = using the finished model on live camera frames. Light work.
  Done by the Pi, by itself, with no laptop needed.

**Coral accelerator: PINNED.** It plugs into the Pi (USB), so adding it later
does not change the PCB or the wiring. Keep the 5 V module sized for 5 A and
leave a little space in the enclosure. Decide at P2 after measuring the model on
the Pi alone. Without it the Pi's CPU runs the model; this probably meets our
2-5 detections-per-second goal but is NOT verified. Its price swings widely
($89-$200) and the Newark listing is unusable (deliveries from Jan 2027).

**Why I chose the 8 GB Pi and pinned the Coral:**
- I said I did not want the 4 GB Pi, even to save money, because the RAM cannot
  be upgraded later and the semester 2 drone work will want the room.
- I asked what I lose without the Coral and why I need a second chip if the Pi
  is already there. I decided that if the Coral can be added later with no
  change to the wiring or PCB, it should simply be pinned and decided at P2.
- I decided not to buy the Pi now.

---

## Decision 9: One USB camera, bought now, used from day one (decided Oct 17)

**What:** **Arducam 1080p HDR autofocus USB camera** (78 degree view, small metal
body), $19.99 on Amazon. It replaces the Raspberry Pi Camera Module 3 and its
ribbon cable, which are removed from the BOM.

**Why:**
- Training photos must come from the **same camera** the turret will use, or
  the model sees a different "look" than it was trained on.
- The camera mount in the CAD depends on the camera's exact size, so choosing
  the final camera now means no redo.
- A USB camera works on the laptop today and plugs into the Pi later. The
  Camera Module 3 only works on a Pi, and we are not buying the Pi yet.

**Plan:** unscrew it from its stand and mount just the case in a 3D-printed
holder.

**Checks when it arrives:**
- The page does not list MJPEG. Confirm **MJPG at 1920x1080, 30 fps**
  (`v4l2-ctl --list-formats-ext` on Linux, or OBS on the laptop). Over USB 2,
  uncompressed 1080p is only a few fps, so MJPEG is required. Return it if
  missing.
- Measure the case with calipers before finishing the mount.

**Trade-off we accepted:** cheaper image quality than a $39-65 camera. If the
project continues, we upgrade, which means retaking the main training dataset.
So collect only a small starter set on this camera to prove the pipeline.

**Why I chose a USB camera now:**
- I want to train on the same camera the turret will use, because a different
  camera changes the data quality and the training.
- I do not want to redo the CAD for the camera mount later.
- I will not buy the Pi now but need the camera now, so it has to work on my
  laptop and later on the Pi. I set a $27 ceiling and chose the Arducam after
  comparing it with an InnoMaker board.
- I plan to take it out of its stand and mount just the case for full control.

---

## Decision 10: Laser is IN Prototype 1; cheap 5 mW module chosen (decided Oct 17)

**What:** In P1 the laptop runs the drone-detection model on frames from the
Arducam USB camera. When it is confident, the laptop sends one message over USB
serial to the STM32, which switches the laser on. No Pi needed in P1.

The laser is a cheap **AREALER 5 mW, 650 nm, 5 V red dot module** (4-pack,
$7.61 at Walmart). The STM32 pin is too weak to power it directly, so an
**IRLZ44N logic-level MOSFET** (2 for $3.60 at Digi-Key, one spare) acts as the
on/off switch, with power coming from 5 V.

**Why I chose this laser setup:** I want to see the laser fire when the model
detects a drone in Prototype 1. I chose the cheap 4-pack over the $25 Quarton to
save money and said not to worry about the maker's guarantee. I approved the
$1.80 MOSFET and the $1.00 camera-cable swaps for the same reason: cost.

---

## Decision 11: Mechanical build and ordering

- A 3D printer is available, so the pan-tilt structure and camera holder are
  printed. Exact **screws and fasteners** are chosen after the CAD (NEMA 17 motor
  mounts are usually M3). The BOM holds a $15 placeholder.
- Wires and a USB cable are already owned.
- **Monday Oct 19** is the P1 order day, after checking what the Purdue ECE shop
  has. Amazon items (motor kits, adapter, jack, camera) go in one order over
  $25. Digi-Key takes the Nucleo (if the ECE shop has none), 2 MOSFETs and the
  surge diode.
- Slow China orders (if any) are placed early, and a $30 "unknowns" allowance is
  in the BOM.

**Why the budget is open:** a friend may help fund the project in exchange for a
resume credit, so I said not to fret too much about the budget. I also asked to
budget for China orders and for things I will only discover while building.

---

## Decision 12: Power protection and filtering on the PCB (decided Oct 29)

Goal: the board survives mistakes and motor noise, and I learn how real power
boards do it. Parts in order, from the power input toward the loads:

| Part | What it does (plain words) | Why it is there |
|---|---|---|
| Barrel jack (main) and XT60 pads (empty) | The jack takes the wall adapter. The XT60 footprint is for a battery later. | Matches my wall plug. See Decision 6. |
| Fuse (5 A for P1, 15 A final) | A thin wire that melts if too much current flows | Stops a short from starting a fire |
| Reverse-polarity protection | A diode or a P-type MOSFET that blocks power if + and - are swapped | A swapped plug would otherwise destroy the chips |
| TVS diode (SMCJ15A) | Clamps sudden voltage spikes, like a pressure-relief valve | Motors and cables make spikes that can pass 15 V |
| Bulk capacitor (100-1000 uF) | A small tank of charge close to the motor drivers | Motors pull current in bursts; the tank keeps the voltage steady |
| Buck module (Pololu) | Efficiently turns 12 V into 5 V | The Pi needs 5 V at up to about 5 A |
| Ferrite bead and small capacitors on the 5 V line | Block fast electrical noise from reaching the Pi | Motor noise can reset a Pi |

**Why a buck and not a linear regulator:** a linear regulator burns the
difference as heat: (12 V - 5 V) x current. At 3 A that is 21 W, which would melt
it. A buck converter wastes only about 5-10 percent. A tiny linear regulator is
fine for small jobs (the laser at 25 mA, or 3.3 V logic).

**Reverse guard kept (Oct 30).** It is one part, either a diode or a P-channel
MOSFET (not both). A plain diode drops about 0.6 V and would burn about 3 W at
5 A, so I lean toward the MOSFET. Final pick in the calculations step.

**What the TVS prevents:** voltage spikes. A motor coil pushes the voltage up
whenever its current changes suddenly, and plugging in a live adapter can make the
cable and capacitors "ring" above 12 V. The SMCJ15A does nothing below about 15 V
and shorts a spike to ground above that. Exact numbers to confirm in the
datasheet.

**Why I chose this set:** I wanted the standard protection a real product uses,
and I wanted to learn what each part does.

**Why I kept the reverse guard:** I saw reversed rails on the bench while testing
laser modules, and I don't want to repeat the same mistake. It protects the 12 V
input, so a backwards supply cannot kill the board.

---

## Decision 13: How the Nucleo connects to the PCB (decided Oct 29)

**What:** design the PCB so the Nucleo **plugs in** (sockets on the PCB that
match the Nucleo's header pins). If that makes the board too big or awkward, the
same signals also go to a plain header, so I can use wires between the Nucleo and
the PCB instead.

**Size (estimate, to check in KiCad):** the Nucleo-144 is about 5.25 x 2.75 in
(133 x 70 mm; check ST's UM1974). A board it stacks on needs to be at least that
big. A side-by-side board with wires could be about 3 x 4 in or smaller.

**Power and data (Oct 30):** the Nucleo is powered by the USB cable from the Pi,
which also carries serial data. The carrier board does not power the Nucleo. Its
signals to the board (STEP, DIR, EN and the laser pin) are 3.3 V from the
Nucleo's own regulator, so no voltage step-down is needed.

**Why I chose "plug in, with a header and wires as a backup":** I want the
finished turret to look clean, but a Nucleo is large and I do not want one
choice to block the whole board. Both options use the same pins.

---

## Still open (not decided)

1. **5 V module for the Pi:** Pololu vs AliExpress (the sealed Amazon USB-C module
   is ruled out, see Decision 5). Lean toward Pololu, not confirmed. It must be
   settled before the PCB layout is final. Target: board design finished and
   ordered Oct 30, hard limit Nov 1.
   - **Reverse guard part:** diode or P-MOSFET (calculations step).
   - **Barrel jack part:** match my adapter's plug size and polarity.
   - **Pi 5 USB power limit** with the camera and Nucleo on USB.
2. **YOLO fine-tune vs from-scratch network.** Parked for now. Note the project
   rule says "self-trained, not pretrained". Fine-tuning a small YOLO on our own
   photos is the practical route; training a tiny network from scratch is a
   stronger story but riskier for the Dec 12 deadline. Resume wording must
   match whichever we do.
3. **Confidence threshold** for firing the laser (decided during P2/P3).
4. **Coral:** pinned, revisit at P2 (decide Nov 23).
5. **Battery: buy vs build** (decided in late November).
6. **Friend's funding and role.** A friend may help fund the project in exchange
   for a resume credit. The role split and who keeps the hardware are not
   defined yet; agree on them so each person's resume claim is honest.
7. **Overall budget.** The original ~$370 target is no longer binding. The BOM
   currently counts about **$540 without optional items** and about **$733 with
   the battery set and Coral**. Real prices will shift as we order.

## Hard rules that do not change

- No weapon. No RF jammer (illegal, FCC).
- Laser is low-power, only fires above the confidence threshold, never aimed at
  people.
- The AI model is self-trained. It makes the real detect/classify decision.
- Breadboard first, then finalize the PCB (PCB and PCB parts ordered by Nov 1 at the latest, target Oct 30).
