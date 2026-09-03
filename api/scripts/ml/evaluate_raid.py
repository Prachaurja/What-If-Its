"""Evaluate the AI detector on the RAID benchmark and print an accuracy table.

RAID (https://github.com/liamdugan/raid) is the largest public AI-text detection
benchmark: ~6M generations across 11 models, multiple domains, with adversarial
(paraphrased / humanised) variants. This script:

  1. loads a RAID split (full, or a --sample for a quick pass)
  2. runs each text through the detector
  3. reports accuracy, TPR, and — most important — FALSE POSITIVE RATE on human
     text, broken down per source model and per domain.

Run this on a machine/Colab with a GPU. The two Falcon-7B models need ~16 GB.

    pip install datasets scikit-learn
    python scripts/ml/evaluate_raid.py --sample 2000
    python scripts/ml/evaluate_raid.py                     # full (slow)

The false-positive rate on human essays is the number that matters for a product
that could get a student wrongly accused. Target: <= 2% on student-essay domains.
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # make api/ importable when run as a script
import argparse, collections, json, sys

def load_raid(sample: int | None):
    from datasets import load_dataset
    # RAID is on the Hub; 'train' has the labels. domain/model/attack are columns.
    ds = load_dataset("liamdugan/raid", split="train")
    if sample:
        ds = ds.shuffle(seed=42).select(range(min(sample, len(ds))))
    return ds

def evaluate(sample: int | None, threshold: float):
    from app.services.ai_detect.binoculars import binoculars_score
    use_ensemble = threshold < 0  # pass --threshold -1 to score the full ensemble
    if use_ensemble:
        from app.services.ai_detect.ensemble import run as ensemble_run
    ds = load_raid(sample)

    # tallies keyed by (dimension, bucket) -> [correct, total]
    overall = [0, 0]
    fp = collections.defaultdict(lambda: [0, 0])   # human texts flagged AI, per domain
    by_model = collections.defaultdict(lambda: [0, 0])
    by_attack = collections.defaultdict(lambda: [0, 0])

    for ex in ds:
        text = ex["generation"]
        if not text or len(text.split()) < 50:
            continue
        is_ai = ex["model"] != "human"
        if use_ensemble:
            r = ensemble_run(text)
            if not r["scored"]:
                continue
            pred_ai = r["prob"] >= 0.5
        else:
            score = binoculars_score(text)
            pred_ai = score < threshold
        correct = pred_ai == is_ai

        overall[0] += correct; overall[1] += 1
        by_model[ex["model"]][0] += correct; by_model[ex["model"]][1] += 1
        if not is_ai:
            dom = ex.get("domain", "unknown")
            fp[dom][0] += pred_ai; fp[dom][1] += 1
        if is_ai:
            atk = ex.get("attack", "none")
            by_attack[atk][0] += correct; by_attack[atk][1] += 1

    def pct(a, b): return f"{100*a/b:5.1f}%" if b else "   n/a"
    print("\n=== Overall ===")
    print(f"accuracy: {pct(*overall)}  (n={overall[1]})")
    print("\n=== Accuracy by source model ===")
    for m, (c, t) in sorted(by_model.items()):
        print(f"  {m:22s} {pct(c,t)}  (n={t})")
    print("\n=== Detection rate by attack (AI text only) ===")
    for a, (c, t) in sorted(by_attack.items()):
        print(f"  {a:22s} {pct(c,t)}  (n={t})")
    print("\n=== FALSE POSITIVE RATE on human text by domain (lower is better) ===")
    for d, (flagged, t) in sorted(fp.items()):
        print(f"  {d:22s} {pct(flagged,t)}  (n={t})")
    print("\nThreshold used:", threshold)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=None, help="subsample size for a quick pass")
    ap.add_argument("--threshold", type=float, default=0.901)
    a = ap.parse_args()
    try:
        evaluate(a.sample, a.threshold)
    except ImportError as e:
        print(f"Missing dependency: {e}\nRun: pip install datasets scikit-learn torch transformers", file=sys.stderr)
        sys.exit(1)
