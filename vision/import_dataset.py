"""Import a public drone dataset into the pipeline as standalone "clips".

Source: Seraphim Drone Detection Dataset (Hugging Face), single-class YOLO
format, CC BY 4.0. https://huggingface.co/datasets/lgrzybowski/seraphim-drone-detection-dataset

Why this exists:
  Our own pipeline turns VIDEO clips into frames. A public dataset is already
  STILL IMAGES with YOLO labels, so there is no video to extract. This script
  downloads one zip batch, SUBSAMPLES a few hundred images (CPU-friendly, and
  enough to prove the pipeline), and lands them into data/frames + data/labels.

Clip-leakage note:
  split.py prevents train/test leakage by splitting BY CLIP (filename prefix
  before the last '_'). Public still images are independent (Seraphim even
  removed near-duplicates), so we give each image its OWN clip id:
  'seraphim-000123_000000.jpg'. That keeps the anti-leakage machinery honest.

This is a STEPPING STONE, not the shipped model. Per the project rules, the
shipped detector must be trained on our own Arducam footage, with that footage
as the held-out test set.

  python import_dataset.py                 # default: ~600 images, seed 42
  python import_dataset.py --n 300 --seed 7
"""
from __future__ import annotations

import argparse
import csv
import random
import shutil
import tempfile
import zipfile
from pathlib import Path

from src.vision.config import load_config

REPO_ID = "lgrzybowski/seraphim-drone-detection-dataset"
# The smaller split: ~905 MB images + ~1 MB labels, one batch.
IMG_ZIP = "test/images/batch_001.zip"
LBL_ZIP = "test/labels/batch_001.zip"
LICENSE = "CC BY 4.0"
PREFIX = "seraphim"


def _download_and_extract(tmp: Path) -> tuple[Path, Path]:
    from huggingface_hub import hf_hub_download

    print(f"Downloading {IMG_ZIP} (~905 MB) and {LBL_ZIP} from {REPO_ID} ...")
    img_zip = hf_hub_download(REPO_ID, IMG_ZIP, repo_type="dataset", local_dir=tmp)
    lbl_zip = hf_hub_download(REPO_ID, LBL_ZIP, repo_type="dataset", local_dir=tmp)

    img_dir = tmp / "x_images"
    lbl_dir = tmp / "x_labels"
    print("Extracting ...")
    with zipfile.ZipFile(img_zip) as z:
        z.extractall(img_dir)
    with zipfile.ZipFile(lbl_zip) as z:
        z.extractall(lbl_dir)
    return img_dir, lbl_dir


def _index_labels(lbl_dir: Path) -> dict[str, Path]:
    """Map label stem -> label path, regardless of nested extract layout."""
    return {p.stem: p for p in lbl_dir.rglob("*.txt")}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config")
    p.add_argument("--n", type=int, default=600, help="how many images to import")
    p.add_argument("--seed", type=int, default=42, help="subsample seed (reproducible)")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    frames_dir: Path = cfg["paths"]["frames"]
    labels_dir: Path = cfg["paths"]["labels"]
    frames_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="seraphim_") as td:
        tmp = Path(td)
        img_dir, lbl_dir = _download_and_extract(tmp)

        all_imgs = sorted(img_dir.rglob("*.jpg"))
        if not all_imgs:
            print("No images found after extraction.")
            return 1
        labels = _index_labels(lbl_dir)
        print(f"Extracted {len(all_imgs)} images, {len(labels)} labels.")

        # Keep only images that have a matching label (clean pairs).
        paired = [im for im in all_imgs if im.stem in labels]
        print(f"{len(paired)} images have a matching label.")

        rng = random.Random(args.seed)
        rng.shuffle(paired)
        chosen = paired[: args.n]
        print(f"Importing {len(chosen)} images (seed {args.seed}) ...")

        rows = []
        for i, src_img in enumerate(chosen):
            clip_id = f"{PREFIX}-{i:06d}"
            name = f"{clip_id}_000000"
            shutil.copy2(src_img, frames_dir / f"{name}.jpg")
            shutil.copy2(labels[src_img.stem], labels_dir / f"{name}.txt")
            rows.append((clip_id, f"{name}.jpg", src_img.name))

    # Log provenance to clips.csv so the import is traceable.
    log_path: Path = cfg["paths"]["clip_log"]
    header = ["clip_id", "filename", "date", "drone", "lighting",
              "distance", "background", "notes"]
    exists = log_path.exists() and log_path.stat().st_size > 0
    with open(log_path, "a", newline="") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(header)
        for clip_id, filename, src_name in rows:
            w.writerow([clip_id, filename, "imported", "public:seraphim",
                        "", "", "", f"src={src_name} license={LICENSE}"])

    # Attribution NOTICE (CC BY 4.0 requires crediting the source).
    notice = frames_dir.parent / "IMPORTED_DATA_NOTICE.md"
    notice.write_text(
        "# Imported data attribution\n\n"
        f"Some frames under data/frames/ named `{PREFIX}-*` are from the\n"
        f"Seraphim Drone Detection Dataset by Lukasz Grzybowski (Seraphim\n"
        f"Defence Systems), {LICENSE}.\n"
        f"Source: https://huggingface.co/datasets/{REPO_ID}\n\n"
        "These are a STEPPING STONE for proving the pipeline. The shipped model\n"
        "must be trained on our own Arducam footage (project requirement).\n"
    )

    print(f"\nDone. Imported {len(rows)} image/label pairs into {frames_dir}")
    print(f"Provenance logged to {log_path}")
    print(f"Attribution written to {notice}")
    print("\nNext: python -m src.vision.split")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
