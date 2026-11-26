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
!python import_dataset.py --n 1200 --seed 42
!python -m src.vision.split
!python -m src.vision.dataset
```
- `import_dataset.py --n 1200 --seed 42` — downloads the public Seraphim drone
  set, takes the SAME reproducible 1200 images (seed fixes it), lands them in
  `data/frames` + `data/labels`. **More data is usually the single biggest
  accuracy win**, so we pull more than the old 600. The zip has ~900 MB of
  images; raise `--n` further if you want (it caps at how many are in the batch).
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
    epochs=80,       # how many full passes over the dataset. More = more
                     # refining, up to a point. Too many risks overfitting.
                     # patience=20 below will stop early if val plateaus.
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
# project/name pin WHERE the eval images + plots are saved, so Step 9b/10 can
# find them. Without these, Ultralytics picks its own folder (runs/detect/val).
metrics = best.val(data="data/dataset/dataset.yaml", split="test",
                   project="experiments/runs", name="eval")
eval_dir = str(metrics.save_dir)   # exact folder for this eval's images/plots
print("eval saved to:", eval_dir)

ft_map50 = round(metrics.box.map50, 3)
ft_map   = round(metrics.box.map, 3)
ft_p     = round(metrics.box.mp, 3)
ft_r     = round(metrics.box.mr, 3)
print("mAP50:   ", ft_map50)
print("mAP50-95:", ft_map)
print("precision:", ft_p)   # <- for a laser turret, this is the one to watch
print("recall:   ", ft_r)
```
Why a separate test set: if you tune by peeking at test, the score stops meaning
anything. We split it off up front and look once, here. For a laser turret,
watch **precision** — a false fire (shooting a bird) is worse than a miss.

**What "genuinely accurate" looks like here.** On this public data a good
fine-tuned run lands roughly mAP50 ~0.8+ with precision ~0.85+. If you are far
below that, the fix is almost never "more epochs" — it is more/better data and
looking at the failures (Step 9b). Numbers alone do not make the model good; the
failure images tell you what to fix.

## Step 9 — The required experiment: from-scratch vs pretrained

You trained pretrained (fine-tuned) in Step 6. Now train the SAME architecture
from RANDOM weights and compare — this is a project requirement, and it decides
which model you ship.

```python
# .yaml instead of .pt = same yolo11n architecture, RANDOM initial weights.
scratch = YOLO("yolo11n.yaml")
scratch.train(
    data="data/dataset/dataset.yaml",
    epochs=80, imgsz=960, batch=16, patience=20,
    project="experiments/runs", name="train_scratch",
)
sm = scratch.val(data="data/dataset/dataset.yaml", split="test")
sc_map50, sc_p, sc_r = round(sm.box.map50, 3), round(sm.box.mp, 3), round(sm.box.mr, 3)
```

### Step 9a — Put them side by side (the actual decision)

```python
# One table so the "which model ships and why" question has a real answer.
print(f"{'model':<14}{'mAP50':>8}{'precision':>12}{'recall':>9}")
print(f"{'fine-tuned':<14}{ft_map50:>8}{ft_p:>12}{ft_r:>9}")
print(f"{'from-scratch':<14}{sc_map50:>8}{sc_p:>12}{sc_r:>9}")
winner = "fine-tuned" if ft_map50 >= sc_map50 else "from-scratch"
print(f"\n==> SHIP: {winner} (higher test mAP50)")
```
With ~1200 images, from-scratch should score clearly WORSE than fine-tuned.
Demonstrating that gap IS the experiment — it shows why transfer learning
matters when data is limited. Record both rows and the winner.

### Step 9b — Look at the failures (do NOT skip — this is the real skill)

The number tells you *how* good; the mistake images tell you *why* it's wrong,
and that is what drives the next round of data. The eval in Step 8 saved
predicted images under the eval run folder. Open them and look.

```python
import glob
from IPython.display import Image, display
# eval_dir came from Step 8. Show the predicted (not the label) images.
for p in sorted(glob.glob(f"{eval_dir}/val_batch*_pred.jpg")):
    print(p); display(Image(p))
```
Ask of each wrong box: what do the misses/false-fires share? Common culprits on
this data: **drone-on-a-screen** (controller display), **drone logos/stickers**,
tiny far drones, backlit sky. Those become targeted data to add next.

## Step 10 — Save everything out of Colab (do NOT skip)

Colab wipes the whole machine when the session ends — code, data, model, plots.
Pull down the three things you cannot regenerate for free: the **weights**, the
**eval plots** (your evidence for the writeup), and the **log**.

```python
from google.colab import files
import shutil

# 1) The shipped model (the winner from Step 9a — adjust the path if needed).
files.download(f"{results.save_dir}/weights/best.pt")

# 2) Eval plots + predicted images, zipped (PR curve, confusion matrix, batches).
#    eval_dir came from Step 8.
shutil.make_archive("eval_evidence", "zip", eval_dir)
files.download("eval_evidence.zip")

# 3) The experiment log. Get a pre-filled entry first by running the project's
#    evaluate script once on the winner — it AUTO-APPENDS date/size/settings/
#    metrics to experiments/log.md (the notebook's model.val() above does not).
!python -m src.vision.evaluate --weights {results.save_dir}/weights/best.pt
files.download("experiments/log.md")
```
On the laptop, sanity-check the downloaded model:
```bash
python -m src.vision.evaluate --weights path\to\best.pt   # re-measures + logs
python -m src.vision.live_detect --weights path\to\best.pt
```

## Step 11 — Finish the log entry (required; this is how you learn)

The `evaluate.py` run in Step 10 auto-filled the date, dataset size, settings and
TEST mAP50/precision/recall. **You** fill in the three lines it leaves blank,
because they need judgment, not just numbers:
- **Goal / hypothesis** — what this run was testing.
- **Failures seen** — the pattern from Step 9b (e.g. "fires at drone-on-screen").
- **Next action** — the data/change that pattern tells you to try.

Also record BOTH the fine-tuned and from-scratch rows from Step 9a and which one
you are shipping. Patterns only appear across logged runs — this is the real ML
skill.

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
