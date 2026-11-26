# Trained models

Our own trained detectors (the real deliverable). Auto-downloaded pretrained
weights (`yolo11n.pt` etc.) stay gitignored; these do not.

## drone-yolo11n-seraphim-v1.pt

- **What:** YOLO11n fine-tuned to detect one class, `drone`.
- **Trained on:** Seraphim Drone Detection Dataset (public, CC BY 4.0),
  1200 images imported via `import_dataset.py --n 1200 --seed 42`, split by clip.
- **Settings:** 80 epochs, imgsz 960, batch 16, patience 20. Trained on Colab GPU.
- **Test-set metrics (held-out, never seen in training):**
  - mAP@50: **0.893**
  - mAP@50-95: 0.519
  - precision: **0.868**   recall: 0.816
- **Status:** stepping-stone / baseline. This is PUBLIC data. The shipped model
  must be trained on our own Arducam hangar footage (collected after
  Thanksgiving), with that footage as the held-out test set.

Use it:

```bash
python -m src.vision.evaluate   --weights models/drone-yolo11n-seraphim-v1.pt
python -m src.vision.live_detect --weights models/drone-yolo11n-seraphim-v1.pt
```
