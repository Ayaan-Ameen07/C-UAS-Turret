# Vision pipeline bring-up — what we did and learned

This note is for teammates picking up the drone-detection work. It explains how
we got the vision pipeline running end to end for the first time, a real bug we
found and fixed, how we brought in public training data, and what the results
do (and do NOT) mean. Read `README.md` first for the pipeline overview; this is
the "how we actually got it running" companion.

## TL;DR

- The pipeline **code** was already fully written (capture -> extract -> split ->
  dataset -> train -> evaluate -> live_detect). What was missing was the
  environment, any data, and any trained weights.
- We set up a virtual environment, installed the deps, and ran a **smoke test**
  that surfaced a **real bug**: `dataset.py` told YOLO where labels were using a
  key Ultralytics ignores, so training could never find labels. We fixed it.
- We wrote `import_dataset.py` to pull a **public drone dataset** (Seraphim, CC
  BY 4.0) so we can prove the pipeline and practice the train/evaluate loop
  before our own Arducam arrives.
- We trained a **throwaway sanity model** (3 epochs, CPU) end to end. It is weak
  on purpose; the point was to prove the plumbing, and it works.

## 1. Environment setup

- Python 3.13, a project-local **virtual environment** at `vision/.venv`
  (isolates our packages so they do not collide with other projects, and makes
  runs reproducible).
- Installed `requirements.txt` plus `huggingface_hub` (for the data import).
- This machine has **CPU-only PyTorch** (`torch 2.x+cpu`, CUDA = False). That is
  fine for light work. **Real training belongs on a GPU** (a teammate Victus
  with an RTX, or free Google Colab). `train.py` runs the same on all three.

Why the CPU/GPU split matters: training nudges ~2.6M model weights over many
passes (epochs) and is heavy; a GPU does it 10-50x faster. Inference (running
the finished model on frames) is light and runs fine on CPU — which is also why
the Raspberry Pi can run the final model later.

## 2. The bug we found (and why it mattered)

**Symptom:** training died with `No labels found in .../data/frames`.

**Root cause:** `dataset.py` wrote a `labels:` key into `dataset.yaml` to point
YOLO at `data/labels/`. **Ultralytics ignores that key.** It finds each label by
taking the image path and swapping the last `/images/` path segment for
`/labels/` (see `ultralytics.data.utils.img2label_paths`). Our frames lived in
`data/frames/` — no `/images/` segment — so the swap did nothing and no labels
were ever found. This would have blocked ALL training, our own data included.

**The fix (in `dataset.py`):** instead of pointing a yaml at a flat folder, we
now **assemble the standard Ultralytics layout**:

```
data/dataset/
  train/images/*.jpg   train/labels/*.txt
  val/images/*.jpg     val/labels/*.txt
  test/images/*.jpg    test/labels/*.txt
  dataset.yaml
```

`dataset.py` reads the split lists from `split.py` and copies each frame +
its label into the right split folder. Why this is the right fix:

- It is the layout Ultralytics documents and expects — no fighting the library,
  nothing that breaks on an upgrade.
- It gives a **physical barrier** between train/val/test. A test frame sits in
  the `test/` folder and literally cannot leak into training. That backstops the
  project's loudest rule (split by clip, never leak) with structure, not just
  trust in a path list.
- `data/labels/` stays the tracked source of truth; `data/dataset/` is
  gitignored, so the assembled copies never bloat the repo.

Trade-off: frames get duplicated into `data/dataset/`. Trivial at our scale.

**Lesson:** a config key that "looks right" can be silently ignored by a
library. The smoke test caught it in minutes on fake data instead of hours into
a real run. Always smoke-test the whole chain before a long job.

## 3. Bringing in public data (`import_dataset.py`)

We cannot train the shipped model yet — that must be our own Arducam footage
(project rule). But the AI requirements also say to use a public dataset first
to learn the pipeline. So:

- **Source:** Seraphim Drone Detection Dataset on Hugging Face. Single-class
  YOLO format (`drone`), **CC BY 4.0** (free to use with attribution). We picked
  it because the format matches our config exactly and the license is explicit.
- **What the script does:** downloads one zip batch (the smaller ~905 MB test
  split), extracts it, **subsamples ~600 images** (fixed seed, reproducible),
  and lands them into `data/frames/` + `data/labels/`. It logs provenance to
  `clips.csv` and writes an attribution NOTICE (CC BY requires credit).
- **Images, not video:** our own pipeline turns video clips into frames. A
  public dataset is already still images with labels, so the import skips
  `capture`/`extract_frames` entirely.

### The clip-leakage subtlety (important)

`split.py` prevents train/test leakage by splitting **by clip** — it reads a
clip id from each filename (the part before the last `_`). Public still images
are independent (Seraphim even removed near-duplicates), so we name each one as
its **own single-frame clip**: `seraphim-000123_000000.jpg`. That keeps the
anti-leakage machinery honest instead of fighting it. Do not rename imported
frames in a way that drops that `<clipid>_<frame>` shape.

### Reproducing the import

```bash
cd vision
python -m pip install -r requirements.txt   # includes huggingface_hub
python import_dataset.py --n 600 --seed 42
python -m src.vision.split
python -m src.vision.dataset
```

The imported labels and the NOTICE are **gitignored** — they are third-party
data, regenerated by running the script. Only the tools (and this writeup) live
in git.

## 4. The sanity training run (and what it means)

We ran a deliberately tiny run to confirm real data flows through:

- Settings: `--epochs 3 --imgsz 416 --batch 8` on CPU (full config is 80 epochs
  at 960px — that goes on a GPU).
- Data: 600 imported images, split 420 train / 120 val / 60 test (by clip).
- Result on the held-out TEST set: **mAP@50 ~0.28, precision ~0.42, recall
  ~0.46**.

**What this means:** the pipeline works end to end on real data, and the model
already learns a real (if weak) signal in 3 epochs. **What it does NOT mean:**
this is not a good model and not our model. It is a stepping stone. The numbers
will climb a lot with the full config on a GPU, and the shipped detector must be
trained on our own Arducam footage with that footage as the test set.

Also note the Seraphim card's honesty: labels were not manually re-checked, and
the set mixes real/marketing/synthetic images. Fine for practice; worth
remembering when reading metrics. Our labeling guide says to spot-check boxes —
do that before trusting any dataset.

## 5. Project location / OneDrive note

The project now lives on a **local drive**, not inside OneDrive. OneDrive syncing
an active dev folder caused file-lock errors during installs and would fight the
many writes that training and dataset assembly produce. Keep the repo on a local
path; let git (not OneDrive) be the version control. The heavy scratch dirs
(`data/`, `experiments/runs/`, `.venv/`) are gitignored and local-only by design.

## 6. What is next

- **Real training on a GPU:** same `python -m src.vision.train` command on the
  Victus or Colab, with the full config. Install the CUDA build of torch there.
- **Failure analysis:** open the wrong predictions `evaluate.py` saves under
  `experiments/runs/eval*`, find what the misses share, and let that drive the
  next round of data. This loop is the real ML skill.
- **From-scratch vs pretrained:** `train.py --from-scratch` is ready for the
  required A/B comparison.
- **Our own data:** once the Arducam arrives, record clips, label them, and
  retrain — the tooling is already built for it.
