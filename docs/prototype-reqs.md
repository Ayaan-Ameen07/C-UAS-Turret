# Prototype requirements

Last updated: Oct 29, 2026

## Prototype 1 — Parts move, AI sees (Window A, Oct 16 – Nov 2)

**Motor half**
- [x] Bench tests done with lab supplies (see `s42c-bringup-tests.md`): pin map,
      EN/STEP/DIR, laser switch
- [ ] Breadboard wiring: Nucleo-144 F746ZG (ECE loan) + two S42C closed-loop motor kits on a
      12 V wall adapter (fuse, surge diode and 1000 uF capacitor on the supply)
- [x] First power-up on a bench supply at 12 V with about a 1 A current limit (done Oct 25);
      read the labels printed on the S42C boards (V1.1 pinout may differ from the
      V1.0 manual); test both kits on arrival (30-day free returns)
- [ ] Send a command (e.g. `PAN:45,TILT:-10`), motors reach that angle
- [ ] **Checkpoint:** at least one motor turning under STM32 control (the Oct 26
      ESP32 fallback date was dropped)
- [ ] Power doesn't brown out under load

**Vision half**
- [ ] Arducam USB camera arrives; confirm MJPG 1920x1080 at 30 fps is listed
      (`v4l2-ctl --list-formats-ext` or OBS); return it if not; measure the case
- [ ] Collect drone footage/photos **with this camera**: different lighting,
      angles, distances and backgrounds, plus non-drone objects (e.g. birds,
      clutter). Film in clips and log each clip's conditions. Start with close/
      bench range in the hangar (Stage 1), reaching into in-hangar flight
      (Stage 2) as time allows
- [ ] Train detection model v1 on the laptop or Colab
- [ ] Model detects a drone in live video, reports a confidence score

**Laser (in Prototype 1)**
- [ ] Laser module wired through the logic-level MOSFET to the Nucleo
- [ ] Laptop runs the model and sends one message over USB serial; the Nucleo
      switches the laser on when a drone is detected with high confidence
      (target: wall or paper only, never at people)

**Mechanical**
- [ ] Pan-tilt frame and camera holder designed (CAD) and printed; screws chosen
      after the CAD (order by Oct 26)

**PCB design (gate before ordering)**
- [ ] Breadboard motor logic confirmed working (boxes above)
- [ ] Power connector decided (**done**: barrel jack plus XT60 footprint) and the
      5 V module chosen (**by Oct 24**), so layout can start
- [ ] Carrier board designed (Nucleo plugs in, with a header/wire option): Nucleo headers, motor and laser connectors,
      power entry (fuse first), surge diode, laser MOSFET, 5 V module socket,
      optional reverse-polarity protection
- [ ] **Fab order target Oct 30, hard limit Nov 1** (exams start Nov 2), with
      connectors and passives ordered the same day, so it ships during Window B

## Prototype 2 — Combined tracking, checkpoint (Window C start, Nov 20)

- [ ] Order the Pi 5 8 GB, power supply, cooler and microSD **by Nov 10**
- [ ] Wire the Raspberry Pi to the Nucleo (serial, or one USB cable into the
      programmer port); Pi on its own wall supply
- [ ] Pi's detections drive motor commands live, using the same Arducam
- [ ] Measure the model's speed on the Pi alone, then decide on the Coral
      (**Nov 23**; it plugs into a Pi USB port, so no wiring or PCB change)
- [ ] Hybrid loop: neural net runs about 2-5 Hz, classical CV (e.g. KCF) tracks
      between checks at about 30 Hz or more
- [ ] No stutter/oscillation during tracking
- [ ] **Decision logged:** continue as planned, or simplify (drop the hybrid CV,
      accept a slower neural-net-only loop)

## Prototype 3 — Final, measured (Window C end, Dec 7)

Matches the full project requirements:
- [ ] Custom carrier PCB installed, replaces the breadboard (Nucleo plugged in)
- [ ] PCB powers the Pi through the 5 V module only after the board has been
      tested and trusted
- [ ] Pan-tilt motors on custom PCB control (final, not breadboard)
- [ ] Self-trained detector running: a small YOLO fine-tuned on our own drone
      data (not threshold-only)
- [ ] Classical CV tracking between AI checks
- [ ] Laser fires only above the confidence threshold (threshold chosen during
      P2/P3)
- [ ] Measured and recorded: accuracy %, lock-on latency, FPS
- [ ] Stress test: bad lighting, partial occlusion
- [ ] Optional: battery power (decide Nov 22, order Nov 24, must arrive before
      Dec 1)
- [ ] Demo video recorded
- [ ] No weapon, no jammer, nothing aimed at people — confirmed
