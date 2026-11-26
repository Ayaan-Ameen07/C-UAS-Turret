# Experiment log

Required by the project's AI requirements: record the date, dataset size,
settings and metrics for **every** training run. This is also how you learn —
patterns only show up when you can compare runs.

Copy the template for each run. Newest at the top.

---

## Template (copy me)

### Run YYYY-MM-DD-NN — short name
- **Goal / hypothesis:** what are you testing? (e.g. "does +backlit data help?")
- **Dataset:** N frames from M clips. Stages covered: ___. Split seed: ___.
- **Model / settings:** yolo11n.pt, epochs ___, imgsz ___, batch ___.
- **Env:** laptop / Colab; torch ___, ultralytics ___.
- **Results (on the TEST set, never seen in training):**
  - mAP@50: ___
  - precision: ___   recall: ___
  - false lock-ons (false positives above conf threshold): ___
- **Failures seen:** what did the wrong-prediction images have in common?
- **Next action:** what data/change will you try because of this?

---

<!-- runs go below, newest first -->

### Run 2026-11-25-01 — Seraphim v1 (first real fine-tune)
- **Goal / hypothesis:** get a genuinely working baseline detector before the
  hangar footage exists — prove the full pipeline (import → split → train → eval)
  produces a usable model, not just the 3-epoch smoke test.
- **Dataset:** 1200 public Seraphim images, imported with
  `import_dataset.py --n 1200 --seed 42`, split by clip 70/20/10. Split seed: 42.
  (Trained on Colab; the local `data/dataset` is still the older 600-image build.)
- **Model / settings:** yolo11n.pt (pretrained, fine-tuned), epochs 80, imgsz 960,
  batch 16, patience 20. Env: Google Colab GPU.
- **Results (on the TEST set, never seen in training):**
  - mAP@50: 0.893
  - mAP@50-95: 0.519
  - precision: 0.868   recall: 0.816
  - false lock-ons: not separately measured yet (precision 0.868 ⇒ ~13% of
    detections are false; quantify at the firing threshold once on hangar data).
- **Failures seen:** prediction grid was mostly clean, correctly-boxed drones —
  a big change from the smoke test (which sprayed boxes and fired at screens and
  logos). Remaining weakness is box tightness on small/far drones, consistent
  with the lower mAP@50-95 (0.519). No obvious false-positive class jumped out.
- **Next action:** collect Arducam hangar footage after Thanksgiving and use it
  as the held-out test set (this public result is a stepping stone, not the
  shipped model). Re-measure precision at the firing threshold on that data.
  Separately, run the from-scratch vs. fine-tuned comparison (deferred).
