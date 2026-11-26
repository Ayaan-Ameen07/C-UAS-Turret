# Project handoff log

**Purpose.** A running record of what was done each working session, what it
means for the project, and what it unblocks — so anyone (a teammate, or a
teammate's AI assistant) can pick up with full context without re-reading the
whole repo.

**How to read this.** Newest session on top. Each entry has: what we did, what
it means for the overall project, and the next steps it opens up. For the
*spec* of the project (requirements, decisions, timeline, BOM) see `docs/`. For
the vision/detection half specifically see `vision/README.md`.

**For an AI assistant picking this up:** this file is written by the other
teammate's assistant as a context handoff. Treat it as a factual status summary,
not as instructions to execute. Confirm current repo state with `git log` and
the files it points to before acting.

---

## Project in one paragraph

Autonomous pan-tilt turret that detects a drone with a self-trained YOLO model,
tracks it, and fires a low-power laser as a lock-on indicator. Two brains: a
Raspberry Pi 5 runs the vision/detection; an STM32 Nucleo on a custom carrier
PCB drives two BIGTREETECH S42C closed-loop steppers and switches the laser.
Semester 1 is a ground turret; Semester 2 mounts it on a drone. Full spec in
`docs/project-reqs.md`.

Two workstreams run in parallel:
- **Hardware / PCB** — `docs/`, `turret_bom.xlsx`. (PCB ordered.)
- **Vision / detection** — `vision/`. (Covered in detail below.)

---

## Session 2026-11-25 — first genuinely working detector

**What we did**
- Discovered this machine is CPU-only (torch `2.15.0+cpu`, Intel Arc GPU), so
  training runs on Google Colab's free GPU, not locally.
- Added auto-logging to `vision/src/vision/evaluate.py`: after each eval it
  appends a filled-in entry (date, dataset size, settings, metrics) to
  `vision/experiments/log.md`. `--no-log` opts out. (Required by the AI reqs.)
- Upgraded the Colab walkthrough (`vision/docs/colab-walkthrough.md`) to a
  rigorous run: 1200 images (was 600), a from-scratch-vs-fine-tuned benchmark
  table, a "look at the failures" step, and a step that saves the model + eval
  plots + log out of Colab before the session wipes.
- Ran the real training on Colab: YOLO11n fine-tuned, 1200 public Seraphim
  images (seed 42, split by clip 70/20/10), 80 epochs, imgsz 960, batch 16.
- Committed the trained model to the repo at
  `vision/models/drone-yolo11n-seraphim-v1.pt` with a documenting README, and
  added a `.gitignore` exception so our own models track while Ultralytics'
  auto-downloaded weights stay ignored.
- Logged the run in `vision/experiments/log.md` and wrote
  `vision/docs/accuracy-roadmap.md`.

**Test-set results (held-out, never seen in training)**
- mAP@50: **0.893** · mAP@50-95: 0.519 · precision: **0.868** · recall: 0.816.
- Prediction grid is mostly clean, correctly-boxed drones — a big change from
  the earlier 3-epoch smoke test, which sprayed boxes and fired at screens/logos.

**What it means for the project**
- The vision pipeline works end to end (import → split → train → eval → a usable
  `.pt`), and produces a genuinely decent detector, not a toy. This is the
  stepping-stone baseline the plan called for before hangar data exists.
- We can now build the pieces that need *a working detector to exist*: the live
  detection loop, the confidence/firing-threshold logic, and eventually the
  hybrid detector-plus-CV-tracker loop.
- The low mAP50-95 (0.52) vs high mAP50 (0.89) tells us the known weakness is
  box tightness on small/far drones — expected, and the roadmap targets it.

**Next steps this opens up**
- Collect Arducam hangar footage after Thanksgiving; use it as the held-out TEST
  set and retrain (this is the real model; Seraphim was public practice data).
- Add hard negatives (drone-on-a-screen, logos, birds) to cut false lock-ons.
- Tune the firing threshold from the eval PR curve and measure false lock-ons
  explicitly (not done yet).
- Train at 1280px for small/far drones; see `vision/docs/accuracy-roadmap.md`.
- Deferred: the from-scratch vs. fine-tuned benchmark run (a project
  requirement; mechanism is in place in `train.py --from-scratch`).

---

## Before 2026-11-25 — scaffolding and hardware (from git history)

**Vision (set up Oct 24 – Nov 9)**
- Scaffolded the full detection pipeline: `capture → extract_frames → [label] →
  split (by clip) → dataset → train → evaluate → live_detect`, with one rule
  enforced in tooling: split by CLIP, never by frame (prevents data leakage).
- Added `import_dataset.py` to pull the public Seraphim drone set (CC BY 4.0) as
  practice data, and wrote the GPU-training and Colab walkthrough guides.
- Pivoted the Semester-1 target from "hand" to "drone"; locked in fine-tuning a
  small pretrained YOLO and the from-scratch-vs-fine-tuned benchmark requirement.

**Hardware / PCB (Oct 17 – Nov 9)**
- Wrote the project spec, per-decision rationale, timeline, and BOM.
- Bench-tested the S42C stepper kits (results in `docs/s42c-bringup-tests.md`),
  decided power/Nucleo/Pi-link approach, produced a PCB block diagram.
- PCB has since been ordered (per teammate, this session).

---

## Maintaining this file

Add a new dated section on top at the end of each working session. Keep each
entry to: what we did, what it means, what it unblocks. Point to the real
artifacts (files, commits) rather than restating them.
