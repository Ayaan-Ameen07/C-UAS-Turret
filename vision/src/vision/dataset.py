"""Assemble the standard Ultralytics dataset layout that train.py / evaluate.py consume.

Reads the train/val/test image lists produced by split.py and MATERIALIZES a
proper YOLO dataset under data/dataset/:

    data/dataset/
      train/images/*.jpg   train/labels/*.txt
      val/images/*.jpg     val/labels/*.txt
      test/images/*.jpg    test/labels/*.txt
      dataset.yaml

Why assemble real folders instead of just pointing a yaml at data/frames/?
  Ultralytics locates each label by swapping the LAST '/images/' segment of the
  image path for '/labels/' (see ultralytics.data.utils.img2label_paths). It does
  NOT read a 'labels:' key. So the images must live under an '/images/' dir with a
  sibling '/labels/' dir. Assembling per-split folders also gives a PHYSICAL
  barrier between train/val/test, so a test frame cannot leak into training even
  if a path list were wrong. data/labels/ stays the tracked source of truth;
  data/dataset/ is gitignored, so these copies don't bloat the repo.

  python -m src.vision.dataset
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import yaml

from .config import load_config


def _assemble_split(split: str, dataset_dir: Path, labels_dir: Path) -> tuple[int, int]:
    """Copy this split's frames + labels into dataset/<split>/{images,labels}.

    Returns (n_images, n_missing_labels). A missing label is only valid as an
    intentional empty negative; here we warn so you notice an unlabeled frame.
    """
    lst = dataset_dir / f"{split}.txt"
    img_out = dataset_dir / split / "images"
    lbl_out = dataset_dir / split / "labels"
    # Clean rebuild so a re-run never mixes stale frames across splits.
    for d in (img_out, lbl_out):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

    n_imgs = 0
    n_missing = 0
    for line in lst.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        src_img = Path(line)
        shutil.copy2(src_img, img_out / src_img.name)
        n_imgs += 1

        src_lbl = labels_dir / (src_img.stem + ".txt")
        dst_lbl = lbl_out / (src_img.stem + ".txt")
        if src_lbl.exists():
            shutil.copy2(src_lbl, dst_lbl)
        else:
            # No label file = treated by YOLO as a negative (no objects).
            dst_lbl.write_text("")
            n_missing += 1
    return n_imgs, n_missing


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    dataset_dir: Path = cfg["paths"]["dataset"]
    labels_dir: Path = cfg["paths"]["labels"]

    for split in ("train", "val", "test"):
        if not (dataset_dir / f"{split}.txt").exists():
            print(f"Missing {dataset_dir / (split + '.txt')}. Run split.py first.")
            return 1

    total_missing = 0
    print("Assembling dataset (copying frames + labels into per-split folders):")
    for split in ("train", "val", "test"):
        n_imgs, n_missing = _assemble_split(split, dataset_dir, labels_dir)
        total_missing += n_missing
        flag = f"  ({n_missing} frames had NO label -> wrote empty)" if n_missing else ""
        print(f"  {split:6}  {n_imgs:>5} images{flag}")

    # Ultralytics reads class names and the split dirs from this yaml.
    data_yaml = {
        "path": str(dataset_dir),
        "train": "train/images",
        "val": "val/images",
        "test": "test/images",
        "names": {i: name for i, name in enumerate(cfg["classes"])},
    }
    out = dataset_dir / "dataset.yaml"
    with open(out, "w") as f:
        yaml.safe_dump(data_yaml, f, sort_keys=False)

    print(f"\nWrote {out}")
    print("Classes:", data_yaml["names"])
    if total_missing:
        print(f"\nNOTE: {total_missing} frame(s) had no matching label in "
              f"{labels_dir}.")
        print("      An empty label is a valid NEGATIVE (no drone). But if you "
              "meant to label it, add the .txt and re-run.")
    print("\nNext: train.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
