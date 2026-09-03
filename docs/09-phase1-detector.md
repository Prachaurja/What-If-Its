# 09 · Phase 1 — the real detector

Phase 0 shipped similarity with no working AI detection. Phase 1 adds a
zero-shot detector that actually works (Binoculars) and an evaluation harness so
every change is measured, not guessed.

## What's in the code

```
api/app/services/ai_detect/
  binoculars.py   zero-shot detector (two-model perplexity ratio)
  ensemble.py     min-length gate, confidence band, verdict buckets (pure logic, unit-tested)
api/scripts/ml/
  evaluate_raid.py        accuracy + false-positive tables on the RAID benchmark
  calibrate_binoculars.py picks the best threshold for your data under an FPR cap
```

`report.run_check(..., run_ai=True)` calls the ensemble automatically. If torch
or the models aren't installed, the check still runs and AI is reported as
"not scored" with a reason — never a crash.

## How Binoculars works

Two models sharing a tokenizer: an **observer** (Falcon-7B) and a **performer**
(Falcon-7B-instruct).

    perplexity        = observer's surprise at the actual text
    cross_perplexity  = observer's surprise at the performer's predictions
    score             = perplexity / cross_perplexity      (lower = more likely AI)

Dividing cancels the "this topic is just predictable" effect that makes plain
perplexity flag formulaic humans. Verified: text the observer finds unsurprising
scores near 0 (P(AI)->1); genuinely surprising text scores ~0.9 (P(AI)~0.5).

## Running it (needs a GPU or ~16 GB RAM)

    pip install torch transformers datasets scikit-learn accelerate

    # quick accuracy pass on 2k RAID samples
    python scripts/ml/evaluate_raid.py --sample 2000

    # tune the threshold for <=2% false positives on human text
    python scripts/ml/calibrate_binoculars.py --sample 4000 --fpr-cap 0.02
    # then put the printed value in api/.env as BINOCULARS_THRESHOLD

Smaller model pair for a laptop test (lower accuracy, but runs):

    BINOCULARS_OBSERVER=gpt2  BINOCULARS_PERFORMER=gpt2-medium  python scripts/ml/evaluate_raid.py --sample 500

## What to look at in the results

The table to care about is **false-positive rate on human text by domain**. A
detector that catches 95% of AI text but flags 10% of real student essays is not
shippable — that's a wrongly-accused student one time in ten. Target: <=2% FPR on
student-essay domains, and report the number honestly in the product.

## Honest limits

- Short text (<150 words) is not scored — the gate is in `ensemble.py`.
- Heavily paraphrased / "humanised" AI text is where Binoculars is weakest; that's
  what the fine-tuned DeBERTa classifier in Phase 1b is for. `ensemble.combine()`
  already accepts its scores, so adding it is a one-line wire-up.
- No detector is certain. The product shows a band and a caveat, never a bare verdict.

## Phase 1b (next)

Fine-tune DeBERTa-v3 on human / AI / AI-paraphrased text (RAID + PERSUADE student
essays + your own multi-model generations), train the logistic-regression stacker,
and calibrate. Scripts land in `scripts/ml/` alongside these two.
