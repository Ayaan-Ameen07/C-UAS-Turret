# How to make the detector more accurate (in payoff order)

Written after the Seraphim v1 run (mAP50 0.893, mAP50-95 0.519, precision 0.868,
recall 0.816). The cheap "train harder" knobs are mostly spent; from here the
gains come from DATA and from targeting the model's specific weakness.

## 1. Better data — by far the biggest lever

The 0.893 is on PUBLIC data that does not look like our hangar. The largest gain
comes from data that matches what the turret will actually see.

- **Our own hangar footage** (planned after Thanksgiving). Train and test on the
  real Arducam, real lighting, real drone, real backgrounds. Use it as the
  held-out TEST set (project requirement). This matters more than everything
  below combined.
- **More images.** We used 1200 of the ~900 MB Seraphim batch. Pull more, or the
  dataset's other batches. Diminishing returns, but real.
- **Hard negatives.** The early model fired at screens, logos, and text. Add
  images of drone-on-a-screen, drone logos/stickers, birds, kites — labeled as
  "no drone." This directly cuts false lock-ons (the costly error for a laser).
- **Label quality.** Public boxes are often loose or occasionally wrong; a few
  bad labels cap the ceiling. Spot-check and tighten them — lifts mAP50-95 most.

## 2. Attack the specific weakness: small / far drones

mAP50-95 (0.52) far below mAP50 (0.89) means the model FINDS drones but boxes
them loosely — classic small-object behavior, and far drones are the turret's
hard case.

- **Higher input resolution.** Trained at 960px; try **1280**. Most direct fix
  for small/far targets. Slower, more GPU memory — drop batch if it OOMs.
- **Collect more far-away footage** specifically, since that is where it is weak.
- Tiling / zoomed crops so small drones appear larger to the network.

## 3. Model + training knobs — smaller gains, try after data

- **Bigger model for comparison.** `yolo11n` (nano) is sized for the Pi.
  Train `yolo11s` too to see the accuracy ceiling. If the Pi (+ Coral) has
  headroom, `s` could ship.
- **Augmentation experiment** (a project Should-have): accuracy with vs. without
  augmentation, tuned to our conditions.
- **Hyperparameter tuning** (lr, etc.): last few percent, not where to start.

## 4. The metric that actually matters for the turret

Raw mAP is not the goal — **precision at the firing threshold** is. A false fire
is worse than a miss.

- Tune `detect.conf_threshold` (now 0.50) from the eval PR curve: pick the point
  where precision stays very high even if recall drops some.
- Measure false lock-ons explicitly (not done yet; noted in experiments/log.md).
- The hybrid CV tracker (KCF, ~30 Hz) covers frames the detector misses, so we
  can afford to bias toward precision.

## Recommended next step

Do NOT chase model knobs yet — that optimizes against public data that does not
match the task. Highest value: hangar footage after Thanksgiving, with hard
negatives (screens, logos, birds) included, labeled carefully, trained at 1280px.
