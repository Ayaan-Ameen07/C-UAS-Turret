# Training on Google Colab — a detailed, learn-as-you-go walkthrough

This is a teaching guide, not just a list of commands. Each step says WHAT to
run, WHY it exists, and WHAT you should see. Follow it top to bottom in a single
Colab session. If you just want the terse version, see `gpu-training.md`.

## What Colab is (and why we use it)

Google Colab is a free Jupyter notebook that runs on Google's machines in your
browser. The important part for us: it can give you a **GPU** for free. Training
a neural net means adjusting ~2.6M model weights over many passes — heavy math
that a GPU does 10-50x faster than a laptop CPU. Our Pavilion only has a CPU, so
instead of installing GPU drivers anywhere, we borrow Google's GPU for an hour.

A notebook is a list of **cells**. You type code in a cell and press Shift+Enter
to run it. Output appears right below the cell. A `!` at the start of a line
means "run this as a terminal command" instead of as Python. Cells share state,
so something set up in an early cell is still there in a later one.

Mental model for the whole session: Colab hands you a blank GPU computer. We
teach it our project (clone the code), give it the tools (install), give it the
data (reproduce the import), train, then grab the result before the machine is
taken away.

---

## Step 0 — Open a notebook and turn on the GPU

1. Go to https://colab.research.google.com and sign in with a Google account.
2. File -> New notebook.
3. **This is the step people forget:** Runtime -> Change runtime type ->
   Hardware accelerator -> **GPU** -> Save. Without this you get a CPU machine
   and training crawls.

Why it matters: the GPU is the entire reason we are here. If you skip this, every
later step still "works" but training takes hours instead of minutes.

---

## Step 1 — Confirm you actually got a GPU

In the first cell, run:

```python
!nvidia-smi
```

Press Shift+Enter.

What this does: `nvidia-smi` is NVIDIA's "show me the GPU" tool. It prints a
table.

What you should see: a table naming a GPU (often a Tesla T4 on free Colab) and a
CUDA version in the top-right. If instead you get "command not found" or an
error, the runtime is not on GPU — go back to Step 0.

Why we check first: it is much nicer to catch "no GPU" now than to wonder later
why training is slow. Verify the foundation before building on it.

---

## Step 2 — Get our code onto the machine

```python
!git clone https://github.com/Ayaan-Ameen07/C-UAS-Turret.git
%cd C-UAS-Turret/vision
```

What this does, line by line:
- `git clone ...` copies our whole repository from GitHub onto the Colab
  machine. This is why we committed and pushed everything first — Colab pulls a
  fresh copy of exactly what is on GitHub.
- `%cd C-UAS-Turret/vision` changes into the `vision/` folder. Note the `%`, not
  `!`: `%cd` is a notebook "magic" that changes the directory **for all later
  cells**. A `!cd` would only change it inside that one cell and then forget —
  a classic beginner trap. We use `%cd` so every later command runs from inside
  `vision/`, which is where all our scripts expect to be.

What you should see: clone progress, then the prompt sitting in
`.../C-UAS-Turret/vision`. You can confirm with `!ls` — you should see
`import_dataset.py`, `configs/`, `src/`, etc.

---

## Step 3 — Install the tools

```python
!pip install ultralytics huggingface_hub
```

What this does: installs the two libraries our code needs that are not already
on Colab:
- `ultralytics` — the YOLO training/inference engine (it pulls in torch too).
- `huggingface_hub` — how `import_dataset.py` downloads the public dataset.

Why we do NOT install the full `requirements.txt` here: Colab already ships a
**GPU build of PyTorch**. If we blindly reinstalled torch from our requirements,
we might replace Colab's GPU torch with a CPU one and lose the whole point. So on
Colab we only add what is missing and leave Colab's torch alone. (On a local GPU
machine like the Victus the story is different — there you install GPU torch
yourself. That is in `gpu-training.md`.)

What you should see: a lot of "Collecting... Installing..." lines ending without
errors. A few dependency warnings in yellow are normal.

### Confirm torch still sees the GPU

```python
import torch
print("CUDA available:", torch.cuda.is_available())
print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none")
```

What you should see: `CUDA available: True` and a GPU name. This is the single
most important check in the whole guide. `True` means training will use the GPU.
If it says `False`, stop — something replaced the GPU torch, and training would
silently run on CPU. (Fix: Runtime -> Disconnect and delete runtime, then start
over from Step 0.)

Why this matters so much: everything downstream "works" either way, so a wrong
answer here does not throw an error — it just makes training 10-50x slower
without telling you. Always verify.

---

## Step 4 — Reproduce the dataset

```python
!python import_dataset.py --n 600 --seed 42
!python -m src.vision.split
!python -m src.vision.dataset
```

What each line does:
- `import_dataset.py --n 600 --seed 42` downloads the public Seraphim drone
  dataset from Hugging Face, takes a reproducible 600-image sample, and lands the
  images in `data/frames/` and their labels in `data/labels/`. The `--seed 42`
  is what makes it the SAME 600 images every time, on any machine — so your run
  matches the Pavilion run and is comparable.
- `split.py` divides those 600 into train/val/test. It splits **by clip** to
  avoid leakage (frames from one source cannot land in both train and test). For
  this public data each image is its own one-frame clip, so it is a clean split.
- `dataset.py` copies the split into the folder layout YOLO expects
  (`data/dataset/train/images`, `.../labels`, and same for val/test) and writes
  `dataset.yaml`, the file that tells YOLO where everything is and that there is
  one class, `drone`.

What you should see: a ~905 MB download (takes a minute or two), then
"Imported 600 image/label pairs", then a split summary like
`train 420 / val 120 / test 60`, then "Wrote .../dataset.yaml".

Want more data? Raise `--n` (e.g. `--n 4000`). More images generally helps, but
this public data has unverified labels and mixes real/marketing/synthetic
images, so returns diminish. 600 is plenty to learn the flow. The model that
actually ships must be trained on our OWN Arducam footage — this is practice.

---

## Step 5 — Train (the real run)

```python
!python -m src.vision.train
```

This uses the full settings in `configs/drone.yaml`: start from pretrained
`yolo11n.pt`, 80 epochs, 960px images, batch 16, with early-stopping patience 20.

### What is actually happening while it runs

Training repeats a loop over the data. One pass over all 600 images is one
**epoch**; we do up to 80. Within each epoch, for each batch of images:

1. **Forward pass:** push the images through the network; it predicts boxes +
   drone-confidence. Early on, mostly wrong.
2. **Loss:** compare predictions to the true labels; get one number for "how
   wrong." You will see three parts scroll by: `box_loss` (box position),
   `cls_loss` (is it a drone?), `dfl_loss` (box-edge sharpness).
3. **Backpropagation:** calculus works out, for each of the ~2.6M weights,
   which direction would lower the loss (the "gradient").
4. **Optimizer step:** nudge every weight a small amount in that direction. The
   step size is the learning rate.

Repeat, and the loss trends down while accuracy on the validation set trends up.
Because we START from pretrained weights (the model already knows generic
vision), we are only teaching it the one new concept "drone" — which is why a few
hundred images is enough. Early-stopping ("patience 20") halts if validation
stops improving, so it will not grind all 80 epochs pointlessly or overfit.

### What you should see

A header line naming the device — it should say your GPU, NOT "CPU". Then a
per-epoch table with the three losses and, after validation, columns `P`
(precision), `R` (recall), `mAP50`, `mAP50-95`. Watch mAP50 climb over epochs.
On a free T4, this run is minutes, not hours. When it ends it prints where the
weights were saved and strips the optimizer from `best.pt`.

- **mAP50** — the headline accuracy (higher is better, 0-1).
- **precision** — of the things it called drones, how many were drones (high =
  few false alarms; important for us, since a false laser fire is worse than a
  miss).
- **recall** — of the real drones, how many it found.

If you hit an out-of-memory error, lower the batch size:
`!python -m src.vision.train --batch 8`.

---

## Step 6 — Evaluate on the held-out test set

```python
!python -m src.vision.evaluate
```

What this does: measures the trained model on the TEST split — images it never
saw during training. This is the honest score; training/val numbers always look
rosier than reality. It also saves prediction images you can open to SEE the
mistakes.

Why the test set is sacred: if you tune your model by peeking at the test set,
the test score stops meaning anything. We split it off at the start and only look
now, once, at the end. This is the difference between a real metric and fooling
yourself.

What you should see: a `=== TEST metrics ===` block with mAP50, precision,
recall. Write these down (see Step 8).

---

## Step 7 — Download the trained model to your computer

```python
from google.colab import files
import glob
best = sorted(glob.glob("experiments/runs/**/weights/best.pt", recursive=True))[-1]
print("Downloading:", best)
files.download(best)
```

What this does: finds the best checkpoint (`best.pt`, the epoch that scored
highest on validation — about 5-6 MB, the ~2.6M trained numbers) and downloads
it to your laptop.

**Why this step is not optional:** Colab is temporary. When the session ends (you
close it, or it times out after idle), **the entire machine is wiped** — code,
data, and your trained model, all gone. The only thing that survives is what you
download. So grab `best.pt` before you walk away.

On the Pavilion later, point the tools at it:
```bash
python -m src.vision.evaluate --weights path\to\best.pt
python -m src.vision.live_detect --weights path\to\best.pt
```

---

## Step 8 — Record the run (required, and this is how you learn)

Open `experiments/log.md` in the repo and add an entry: the date, that it was
600 images seed 42, the settings (yolo11n.pt, 80 epochs, 960px), and the TEST
mAP50 / precision / recall from Step 6. Note anything the failure images in Step
6 had in common (all backlit? all tiny drones?).

Why: patterns only show up when you can compare runs. This log is required by the
project's AI requirements, and the "look at failures -> collect targeted data ->
retrain -> compare" loop is the actual machine-learning skill, more than any
single number.

---

## Optional — the required from-scratch vs pretrained experiment

The project requires training the same architecture two ways and comparing. You
already did the pretrained one (Step 5). Now run the from-scratch one:

```python
!python -m src.vision.train --from-scratch
!python -m src.vision.evaluate
```

`--from-scratch` starts the SAME network from RANDOM weights instead of
pretrained ones, so it has to learn to see from zero. With only 600 images it
will score clearly worse — and showing that gap IS the experiment. Log both runs
and compare. This demonstrates why transfer learning (starting from pretrained
weights) matters when data is limited.

---

## If something goes wrong

- **Training says "CPU", or Step 3's check printed `False`:** the GPU torch got
  replaced or the runtime is not GPU. Runtime -> Disconnect and delete runtime,
  then redo from Step 0.
- **"No such file" / scripts not found:** you are not in `vision/`. Re-run the
  `%cd C-UAS-Turret/vision` cell (Step 2). Confirm with `!ls`.
- **Out of memory during training:** add `--batch 8` (or `--batch 4`).
- **Session disconnected mid-run:** free Colab has time limits. Just start over;
  the data reproduces from the same seed. For long runs, do import + train in one
  sitting and download `best.pt` promptly.
