"""Measure the model honestly on the TEST set, and SAVE its mistakes.

The numbers (mAP, precision, recall) tell you how good the model is. The saved
mistake images tell you WHY it's wrong — and that's what drives the next round
of data collection. Looking at failures is the single most valuable habit in
practical ML, so this script makes it easy.

For a laser turret, remember: a FALSE POSITIVE (firing at a bird) is worse than
a false negative (missing a drone). So watch precision at your firing threshold.

  python -m src.vision.evaluate
  python -m src.vision.evaluate --weights experiments/runs/train/weights/best.pt
"""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from .config import load_config


def _find_best_weights(cfg: dict) -> Path | None:
    runs = cfg["paths"]["runs"]
    candidates = sorted(runs.glob("**/weights/best.pt"))
    return candidates[-1] if candidates else None


def _count_split(dataset_dir: Path, split: str) -> int:
    """Number of images materialized for a split (0 if the folder is missing)."""
    img_dir = dataset_dir / split / "images"
    if not img_dir.exists():
        return 0
    return sum(1 for p in img_dir.iterdir() if p.is_file())


def _append_log_entry(cfg: dict, weights: Path, conf: float, metrics) -> None:
    """Append a filled-in run entry to experiments/log.md.

    Captures the numbers automatically (date, weights, dataset size, conf,
    mAP/P/R). The 'Failures seen' and 'Next action' lines are left blank on
    purpose — those need your eyes on the saved prediction images.
    """
    log_path = cfg["paths"]["runs"].parent / "log.md"
    dataset_dir = cfg["paths"]["dataset"]
    n_train = _count_split(dataset_dir, "train")
    n_val = _count_split(dataset_dir, "val")
    n_test = _count_split(dataset_dir, "test")

    # Pull metrics defensively — attribute names can shift across versions.
    def _fmt(getter) -> str:
        try:
            return f"{getter():.3f}"
        except Exception:
            return "?"

    scratch = "yes" if weights.name and "scratch" in str(weights).lower() else "see run"
    entry = (
        f"\n### Run {date.today().isoformat()} — eval ({weights.parent.parent.name})\n"
        f"- **Goal / hypothesis:** _(fill in)_\n"
        f"- **Dataset:** train {n_train} / val {n_val} / test {n_test} images "
        f"(materialized in data/dataset). Split seed: {cfg['split']['seed']}.\n"
        f"- **Model / settings:** weights `{weights}`, conf {conf}. "
        f"From-scratch: {scratch}.\n"
        f"- **Results (TEST split):**\n"
        f"  - mAP@50: {_fmt(lambda: metrics.box.map50)}\n"
        f"  - mAP@50-95: {_fmt(lambda: metrics.box.map)}\n"
        f"  - precision: {_fmt(lambda: metrics.box.mp)}   "
        f"recall: {_fmt(lambda: metrics.box.mr)}\n"
        f"- **Failures seen:** _(open eval images, note what the misses share)_\n"
        f"- **Next action:** _(what data/change to try next)_\n"
    )

    # Create from a minimal header if the file is somehow missing.
    if not log_path.exists():
        log_path.write_text("# Experiment log\n")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)
    print(f"\nLogged this run to {log_path}")
    print("  -> fill in Goal, Failures seen, and Next action by hand.")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config")
    p.add_argument("--weights", help="path to best.pt (default: latest run)")
    p.add_argument("--conf", type=float, help="confidence threshold for the "
                   "failure dump (default: config detect.conf_threshold)")
    p.add_argument("--no-log", action="store_true",
                   help="don't append this run to experiments/log.md "
                        "(use for throwaway/debug evals)")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_yaml = cfg["paths"]["dataset"] / "dataset.yaml"
    if not data_yaml.exists():
        print(f"Missing {data_yaml}. Run dataset.py first.")
        return 1

    try:
        from ultralytics import YOLO
    except ImportError:
        print("ultralytics not installed. python -m pip install -r requirements.txt")
        return 1

    weights = Path(args.weights) if args.weights else _find_best_weights(cfg)
    if not weights or not weights.exists():
        print("No trained weights found. Run train.py first, or pass --weights.")
        return 1

    conf = args.conf if args.conf is not None else cfg["detect"]["conf_threshold"]
    print(f"Evaluating {weights} on the TEST split (conf={conf}) ...")

    model = YOLO(str(weights))

    # Metrics on the held-out TEST set (split='test' uses test.txt from the yaml).
    metrics = model.val(data=str(data_yaml), split="test", conf=conf,
                        project=str(cfg["paths"]["runs"]), name="eval")

    # Ultralytics exposes the headline numbers here.
    try:
        print("\n=== TEST metrics ===")
        print(f"  mAP@50:      {metrics.box.map50:.3f}")
        print(f"  mAP@50-95:   {metrics.box.map:.3f}")
        print(f"  precision:   {metrics.box.mp:.3f}")
        print(f"  recall:      {metrics.box.mr:.3f}")
    except Exception as e:  # metric attribute names can shift across versions
        print(f"(could not read summary metrics cleanly: {e})")
        print("See the eval run folder for plots (PR curve, confusion matrix).")

    # Auto-log the run (required by the AI requirements). --no-log opts out.
    if not args.no_log:
        try:
            _append_log_entry(cfg, weights, conf, metrics)
        except Exception as e:
            print(f"(could not write log entry: {e})")

    print(f"\nPlots + predictions saved under {cfg['paths']['runs']}/eval*")
    print("ACTION: open the predicted images, find what the failures share,")
    print("        film targeted data for that case, retrain. Log it all.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
