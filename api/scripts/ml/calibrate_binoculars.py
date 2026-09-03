"""Find the best Binoculars threshold on a labelled validation set.

Sweeps thresholds, and for each reports accuracy and the human false-positive
rate, then picks the threshold with the highest accuracy subject to FPR <= a cap
(default 2%). This is how you tune the detector for YOUR data rather than trusting
the paper's default. Writes the chosen threshold to data/binoculars_threshold.json.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

def main(sample, fpr_cap):
    from datasets import load_dataset
    from app.services.ai_detect.binoculars import binoculars_score
    import numpy as np

    ds = load_dataset("liamdugan/raid", split="train").shuffle(seed=1).select(range(sample))
    scores, labels = [], []
    for ex in ds:
        t = ex["generation"]
        if t and len(t.split()) >= 50:
            scores.append(binoculars_score(t)); labels.append(ex["model"] != "human")
    scores, labels = np.array(scores), np.array(labels)

    best = None
    for thr in np.linspace(scores.min(), scores.max(), 200):
        pred = scores < thr
        acc = (pred == labels).mean()
        human = ~labels
        fpr = (pred & human).sum() / max(human.sum(), 1)
        if fpr <= fpr_cap and (best is None or acc > best["accuracy"]):
            best = {"threshold": float(thr), "accuracy": float(acc), "fpr": float(fpr)}

    Path("data").mkdir(exist_ok=True)
    Path("data/binoculars_threshold.json").write_text(json.dumps(best, indent=2))
    print("Best under FPR cap:", best)
    print("Set BINOCULARS_THRESHOLD to this value in your .env")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=4000)
    ap.add_argument("--fpr-cap", type=float, default=0.02)
    a = ap.parse_args()
    main(a.sample, a.fpr_cap)
