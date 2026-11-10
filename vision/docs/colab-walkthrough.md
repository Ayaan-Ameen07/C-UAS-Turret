# Training on Google Colab — write the training yourself (learn-as-you-go)

This is a teaching guide where **you write the training code**, not a wrapper.
Data prep (download/split/assemble) stays as reusable script calls — no point
hand-retyping a 900 MB download — but the TRAINING itself you type cell by cell
using the Ultralytics Python API, so you see and control every piece: loading
the model, configuring the run, driving it, and reading the results.

Note on levels: here you drive training with the Ultralytics API (`model.train`).
Ultralytics still runs the low-level loop (forward/loss/backprop/optimizer step)
inside that call — that is how ~all real YOLO work is done; nobody rewrites
YOLO's internals. If you later want to hand-write the raw forward/backward/step
loop and literally type the lines that change the weights, that is a separate
module on a simpler model (see the "Going deeper" note at the end).

## How a Colab notebook works

Colab is a free browser notebook that can give you a **GPU**. Training adjusts
~2.6M model weights over many passes — heavy math a GPU does 10-50x faster than
a CPU. A notebook is a list of **cells**; type code, press Shift+Enter to run,
output appears below. A line starting with `!` runs as a terminal command; `%`
is a notebook "magic"; everything else is Python. Cells share state, so a
variable from an earlier cell is still alive in a later one.

---

## Step 0 — New notebook, GPU on

1. https://colab.research.google.com -> sign in -> File -> New notebook.
2. Runtime -> Change runtime type -> Hardware accelerator -> **GPU** -> Save.
   (Skip this and everything runs, but on a slow CPU.)

## Step 1 — Confirm the GPU (cell)

```python
!nvidia-smi
```
Expect a table naming a GPU (often a T4). Error/"not found" => redo Step 0.
Verify the foundation before building on it.

## Step 2 — Get the code (cell)

```python
!git clone https://github.com/Ayaan-Ameen07/C-UAS-Turret.git
%cd C-UAS-Turret/vision
```
`git clone` pulls our repo from GitHub. `%cd` (with `%`, not `!`) changes the
directory for ALL later cells — `!cd` would only last inside one cell. Our
scripts expect to run from `vision/`. Confirm with `!ls`.

## Step 3 — Install tools + verify GPU torch (cells)

```python
!pip install ultralytics huggingface_hub
```
Only the two libraries Colab lacks. We do NOT reinstall `requirements.txt`
because Colab already ships a **GPU** build of torch and we must not replace it
with a CPU one.

```python
import torch
print("CUDA available:", torch.cuda.is_available())
print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none")
```
**Must print `True`.** This is the one check that fails SILENTLY if wrong —
training would run on CPU with no error, just 10-50x slower. `False` => Runtime
-> Disconnect and delete runtime, start over.

## Step 4 — Reproduce the dataset (cell; reusable scripts)

```python
!python import_dataset.py --n 600 --seed 42
!python -m src.vision.split
!python -m src.vision.dataset
```
- `import_dataset.py --n 600 --seed 42` — downloads the public Seraphim drone
  set, takes the SAME reproducible 600 images (seed fixes it), lands them in
  `data/frames` + `data/labels`.
- `split.py` — divides into train/val/test **by clip** (no leakage). Each public
  image is its own one-frame clip.
- `dataset.py` — copies into YOLO's expected `train/val/test` + `images/labels`
  layout and writes `dataset.yaml` (tells YOLO where data is; one class `drone`).

These are project tooling, kept as scripts on purpose. Raise `--n` for more data.

---

# The training — YOU write these cells

From here you type the training using the Ultralytics Python API. Run each cell
and read its output; the comments explain what each line does.

## Step 5 — Load the model

```python
from ultralytics import YOLO

# Load yolo11n with PRETRAINED weights (the .pt). "nano" = smallest YOLO11,
# ~2.6M weights: small and fast enough to run on the Pi later. Pretrained means
# the weights already learned general vision (edges/shapes/objectness) on a big
# dataset, so we only have to teach the ONE new concept: "drone".
model = YOLO("yolo11n.pt")

# Peek at the model. (Optional, but good to see what you loaded.)
print(type(model))
print("task:", model.task)        # -> 'detect'
```

Why load from `.pt` and not `.yaml`: `.pt` = pretrained weights (fine-tuning
start); `.yaml` = same architecture but RANDOM weights (from-scratch). We start
pretrained because with only a few hundred images, starting from random would
learn far worse. (You will run the random version yourself in Step 9.)

## Step 6 — Kick off training and understand the knobs

```python
# model.train runs the actual loop internally (forward -> loss -> backprop ->
# optimizer step), once per batch, for each epoch. YOU set the knobs here.
results = model.train(
    data="data/dataset/dataset.yaml",  # where the train/val data + class names are
    epochs=80,       # how many full passes over the 600 images. More = more
                     # refining, up to a point. Too many risks overfitting.
    imgsz=960,       # input image size. Bigger helps SMALL objects (drones are
                     # small/far) but is slower + uses more GPU memory.
    batch=16,        # images processed together per step. Bigger = steadier
                     # gradients but more memory. Lower this if you hit OOM.
    patience=20,     # EARLY STOPPING: if val stops improving for 20 epochs,
                     # stop. Prevents wasted epochs and curbs overfitting.
    project="experiments/runs",  # where outputs/weights are saved
    name="train_api",            # subfolder name for this run
)
```

While it runs, read the per-epoch table. These are the loop's own numbers:
- `box_loss` — how off the box positions are.
- `cls_loss` — how wrong about "is this a drone".
- `dfl_loss` — a term that sharpens box edges.
All three should trend DOWN. After each epoch it validates and prints `P`
(precision), `R` (recall), `mAP50`, `mAP50-95` — these should trend UP. The
header line names the device; it must be your GPU, not CPU. On a T4 this is
minutes.

What "training" means here, concretely, each step: push a batch through (forward
pass) -> compare predictions to the true boxes to get a loss -> backprop
computes, for all ~2.6M weights, which way to nudge each to lower the loss ->
the optimizer nudges them. Repeat. That is literally how the weights change;
`model.train` is running that loop for you.

If you get a CUDA out-of-memory error, re-run Step 6 with `batch=8` (or `4`).

## Step 7 — Inspect what you just trained (read the results object)

```python
# model.train returned a results object; the best checkpoint path is here:
print("Saved to:", results.save_dir)

# Where the weights live:
import glob
weights = sorted(glob.glob(f"{results.save_dir}/weights/*.pt"))
print("weights files:", weights)   # expect best.pt and last.pt
```
`best.pt` = the epoch that scored best on validation (what you keep). `last.pt` =
the final epoch. You are reading the output yourself instead of a script telling
you — this is the habit that builds real understanding.

## Step 8 — Evaluate honestly on the TEST set

```python
# Load the best weights and measure on the HELD-OUT test split (never seen in
# training). This is the honest number; train/val always look rosier.
best = YOLO(f"{results.save_dir}/weights/best.pt")
metrics = best.val(data="data/dataset/dataset.yaml", split="test")

print("mAP50:   ", round(metrics.box.map50, 3))
print("mAP50-95:", round(metrics.box.map, 3))
print("precision:", round(metrics.box.mp, 3))
print("recall:   ", round(metrics.box.mr, 3))
```
Why a separate test set: if you tune by peeking at test, the score stops meaning
anything. We split it off up front and look once, here. For a laser turret,
watch **precision** — a false fire (shooting a bird) is worse than a miss.

## Step 9 — The required experiment: from-scratch vs pretrained

You trained pretrained in Step 6. Now train the SAME architecture from RANDOM
weights and compare — this is a project requirement.

```python
# .yaml instead of .pt = same yolo11n architecture, RANDOM initial weights.
scratch = YOLO("yolo11n.yaml")
scratch.train(
    data="data/dataset/dataset.yaml",
    epochs=80, imgsz=960, batch=16, patience=20,
    project="experiments/runs", name="train_scratch",
)
scratch_metrics = scratch.val(data="data/dataset/dataset.yaml", split="test")
print("FROM-SCRATCH mAP50:", round(scratch_metrics.box.map50, 3))
```
With only 600 images, from-scratch should score clearly WORSE than pretrained.
Demonstrating that gap IS the experiment — it shows why transfer learning
matters when data is limited. Log BOTH test numbers.

## Step 10 — Download your model (do NOT skip)

```python
from google.colab import files
files.download(f"{results.save_dir}/weights/best.pt")
```
Colab wipes the whole machine when the session ends — code, data, model. The
downloaded `best.pt` (~5-6 MB, your ~2.6M trained weights) is the ONLY thing that
survives. On the Pavilion:
```bash
python -m src.vision.evaluate --weights path\to\best.pt
python -m src.vision.live_detect --weights path\to\best.pt
```

## Step 11 — Log the run (required; this is how you learn)

In `experiments/log.md` record: date; 600 images, seed 42; settings (yolo11n,
80 epochs, 960px, batch 16); TEST mAP50/precision/recall for BOTH the pretrained
and from-scratch runs; and anything the failure images had in common. Patterns
only appear across logged runs — this is the real ML skill.

---

## Reminders

- This is PUBLIC data — a stepping stone. The shipped model must train on our
  OWN Arducam footage, with that footage as the held-out test set.
- `model.train`/`model.val` are the Ultralytics API; you are driving them and
  reading their outputs, which is how real YOLO work is done.

## Going deeper (optional, later)

If you want to hand-write the raw forward/loss/`backward()`/`optimizer.step()`
loop and literally type the lines that update the weights, that is best done on a
small CNN classifier (YOLO's loss/label-assignment is too complex to hand-roll
usefully). It also maps to this project's classifier stretch goal. Ask for the
"Level 2 raw-PyTorch loop" module when you want it.
