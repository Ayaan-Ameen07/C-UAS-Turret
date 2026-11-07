# GPU training — run the real training on a GPU

The Pavilion we set the pipeline up on has **CPU-only PyTorch**, which is fine
for light work but too slow for a real training run (80 epochs at 960px would
take hours). Training is heavy — it nudges ~2.6M model weights over many passes
— so it belongs on a GPU. Inference (running the finished model) stays light and
runs fine on CPU, including the Raspberry Pi later.

This guide covers two ways to get a GPU:

- **Option A — Google Colab:** free GPU in the browser, zero setup on any
  laptop. Best if you just want to train now.
- **Option B — A local NVIDIA GPU (e.g. the teammate Victus/RTX):** faster for
  repeated runs, data stays put, but needs the right CUDA-matched PyTorch.

**The key idea for both:** everything is in git. You reproduce the environment
with **GPU PyTorch** (the one difference from the CPU setup) and run the exact
same `train.py`. The dataset is reproducible from `import_dataset.py` with the
same seed, so you do not have to copy image files around.

---

## Reproduce the data on any machine (both options need this)

The importer re-downloads the same public images for a given seed, so a fresh
machine gets the IDENTICAL dataset:

```bash
cd vision
python import_dataset.py --n 600 --seed 42   # same data as the Pavilion
python -m src.vision.split
python -m src.vision.dataset
```

(When our own Arducam data exists, you would sync that instead — but the public
stepping-stone data is fully reproducible this way.)

---

## Option A — Google Colab (free GPU, no local setup)

1. Go to https://colab.research.google.com and start a new notebook.
2. **Turn on the GPU:** Runtime -> Change runtime type -> Hardware accelerator
   -> GPU -> Save.
3. In a cell, confirm the GPU is there:
   ```python
   !nvidia-smi
   ```
4. Get the code. Easiest is to clone the repo:
   ```python
   !git clone https://github.com/Ayaan-Ameen07/C-UAS-Turret.git
   %cd C-UAS-Turret/vision
   ```
5. Install deps. Colab already ships a CUDA build of torch, so just add the rest:
   ```python
   !pip install ultralytics huggingface_hub
   ```
6. Reproduce the data (same three commands as above):
   ```python
   !python import_dataset.py --n 600 --seed 42
   !python -m src.vision.split
   !python -m src.vision.dataset
   ```
7. Train with the FULL config (this is the real run):
   ```python
   !python -m src.vision.train
   ```
8. Download the trained weights to your computer:
   ```python
   from google.colab import files
   import glob
   best = sorted(glob.glob("experiments/runs/**/weights/best.pt", recursive=True))[-1]
   files.download(best)
   ```

Notes:
- Colab sessions time out and wipe the disk. Do the import + train in one
  sitting, and download `best.pt` before you close it.
- The free GPU is enough for yolo11n at 960px. If it runs out of memory, lower
  the batch size: `!python -m src.vision.train --batch 8`.

---

## Option B — Local NVIDIA GPU (the Victus)

### B1. Check what the machine has

```bash
nvidia-smi          # shows the GPU + the CUDA version it supports (top right)
python --version    # 3.10-3.13 all fine
```

Note the **CUDA version** `nvidia-smi` reports (e.g. 12.6, 12.8). You pick the
matching torch wheel tag from it: CUDA 12.6 -> `cu126`, 12.8 -> `cu128`, etc.

If `nvidia-smi` is not found, install the NVIDIA driver first (GeForce
Experience / nvidia.com). You do NOT need to install the full CUDA Toolkit — the
torch wheel bundles the CUDA runtime it needs.

### B2. Make a fresh virtual environment

Do NOT copy the Pavilion's `.venv` — it has the CPU torch baked in. Make a clean
one on the Victus:

```bash
cd vision
python -m venv .venv
.\.venv\Scripts\activate          # Windows PowerShell
# source .venv/bin/activate       # Linux/macOS
python -m pip install --upgrade pip
```

### B3. Install GPU PyTorch FIRST (the one real difference)

Install the CUDA-tagged torch from PyTorch's own index, matching the tag from
B1. Example for CUDA 12.6:

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
```

Swap `cu126` for whatever matches (`cu128`, `cu130`, ...). The current official
install line is always at https://pytorch.org/get-started/locally (pick
Stable / your OS / Pip / CUDA).

Then install the rest WITHOUT letting it pull the CPU torch back in:

```bash
pip install ultralytics opencv-python pyyaml numpy pandas tqdm matplotlib pyserial huggingface_hub
```

(We install torch separately rather than from requirements.txt so the GPU wheel
is not overwritten by the generic `torch` line.)

### B4. Verify the GPU is actually used

```bash
python -c "import torch; print('cuda', torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')"
```

You want `cuda True` and your GPU's name. If it says `False`, the CPU wheel got
installed — uninstall and redo B3:
```bash
pip uninstall -y torch torchvision
```

### B5. Reproduce the data and train

```bash
python import_dataset.py --n 600 --seed 42
python -m src.vision.split
python -m src.vision.dataset
python -m src.vision.train           # full config: 80 epochs, 960px
```

Ultralytics auto-detects and uses the GPU. Watch the first few lines of training
output — it names the device (should be your GPU, not "CPU").

### B6. Get the weights back to Ayaan

The trained model is `experiments/runs/train*/weights/best.pt` (~5-6 MB).
`experiments/runs/` is gitignored (training outputs do not belong in git), so
send `best.pt` directly — Drive, a file transfer, or attach it. On the Pavilion,
drop it anywhere and point the tools at it:
```bash
python -m src.vision.evaluate --weights path\to\best.pt
python -m src.vision.live_detect --weights path\to\best.pt
```

---

## The from-scratch vs pretrained experiment (required)

The project requires training the same architecture two ways and comparing them.
On the GPU, run both and log each in `experiments/log.md`:

```bash
python -m src.vision.train                 # (B) fine-tuned from pretrained weights
python -m src.vision.train --from-scratch  # (A) random init, same architecture
```

`--from-scratch` swaps `yolo11n.pt` (pretrained) for `yolo11n.yaml` (random
weights). Evaluate both on the SAME test split and record mAP/precision/recall
for each. Expect the pretrained one to win clearly with only a few hundred
images — that is the point of the comparison.

---

## What to expect

- The full run will score much higher than the Pavilion's throwaway 3-epoch
  sanity run (~0.28 mAP). But remember: this is still PUBLIC data — a stepping
  stone. The shipped model must be trained on our own Arducam footage, with that
  footage as the held-out test set (project rule).
- Record every run in `experiments/log.md`: date, dataset size, settings,
  metrics. That log is required and it is how the failure-analysis loop works.
