# 10 · Phase 1b — DeBERTa classifier + stacker

Binoculars (Phase 1) catches AI text from any model but is weakest on
paraphrased / "humanised" text — the exact trick students and content mills use
to evade detection. Phase 1b adds a supervised classifier trained on that case,
and a stacker that fuses the two detectors into one calibrated score.

## What's in the code

```
api/app/services/ai_detect/
  deberta.py    3-class classifier (human / ai / ai_paraphrased) + per-window scores
  stacker.py    logistic-regression + calibration over both detectors (+ transparent fallback)
  ensemble.py   now runs Binoculars + DeBERTa -> stacker -> band + verdict
api/scripts/ml/
  make_dataset.py    builds the 3-class training set (HC3 + T5 paraphraser)
  train_deberta.py   fine-tunes DeBERTa-v3 -> data/ai_classifier/
  train_stacker.py   fits the stacker on held-out RAID -> data/stacker.joblib
  evaluate_raid.py   now supports --threshold -1 to score the FULL ensemble
```

Everything degrades gracefully: if the DeBERTa model isn't trained yet,
`deberta.is_available()` is False and the ensemble runs on Binoculars alone; if
the stacker isn't trained, `stacker.predict()` uses a transparent weighted blend.
The check never crashes for a missing model.

## Why three classes

`human / ai / ai_paraphrased`. The third class is the whole point — you cannot
detect humanised text without training on examples of it. `make_dataset.py`
manufactures them by pushing AI answers through a paraphraser (a free stand-in
for QuillBot / Undetectable.ai). The classifier's "AI-involved" probability is
P(ai) + P(ai_paraphrased); the paraphrase probability alone drives the UI's
"looks humanised" note and shifts the stacker's weight toward DeBERTa.

## Why a stacker, not an average

Averaging trusts both detectors equally everywhere. The stacker learns *when* to
trust each: lean on DeBERTa when it detects paraphrasing, on Binoculars for long
text. Isotonic calibration then makes the number honest — a reported 0.80 means
AI-involved ~80% of the time, which is what lets you show a score responsibly.

## Training (Colab, one GPU)

```bash
pip install -e ".[ml]" joblib
# 1. build the dataset (GPU speeds up the paraphraser)
python scripts/ml/make_dataset.py --n 3000
# 2. fine-tune the classifier (~20 min on a T4)
python scripts/ml/train_deberta.py
# 3. fit the stacker on held-out RAID
python scripts/ml/train_stacker.py --sample 3000
# 4. measure the full ensemble
python scripts/ml/evaluate_raid.py --sample 2000 --threshold -1
```

Copy `data/ai_classifier/` and `data/stacker.joblib` back to the server (or object
storage) and the ensemble picks them up automatically.

## What to compare

Run `evaluate_raid.py` twice — once with the default threshold (Binoculars only)
and once with `--threshold -1` (full ensemble) — and compare the **detection rate
on the paraphrased/adversarial attack rows**. That delta is what Phase 1b buys you.
Keep watching the human false-positive rate; the stacker should not raise it.

## Next

Phase 2: move detection into the Celery worker (it's already a pure function of
text, so it lifts straight in) and add auth/orgs so checks run in the background
and stay isolated per organisation.
