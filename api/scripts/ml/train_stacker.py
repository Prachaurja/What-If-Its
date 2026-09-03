"""Train the stacker: logistic regression + isotonic calibration on top of the
two detectors. Produces data/stacker.joblib, loaded by stacker.predict().

Needs a labelled *validation* set that is NOT the DeBERTa training data (else the
stacker overfits to DeBERTa's memorised examples). Simplest source: a held-out
slice of RAID. For each text we compute both detectors' outputs + cheap features,
then fit.

    pip install datasets transformers torch scikit-learn joblib
    python scripts/ml/train_stacker.py --sample 3000
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # make api/ importable when run as a script
import argparse, joblib
from pathlib import Path

def main(sample: int):
    from datasets import load_dataset
    from sklearn.linear_model import LogisticRegression
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from app.services.ai_detect.binoculars import detect as bino
    from app.services.ai_detect.deberta import classify, is_available
    from app.services.ai_detect.stacker import features

    if not is_available():
        print("Train DeBERTa first (scripts/ml/train_deberta.py)."); return

    ds = load_dataset("liamdugan/raid", split="train").shuffle(seed=7).select(range(sample))
    X, y = [], []
    for ex in ds:
        t = ex["generation"]
        if not t or len(t.split()) < 60:
            continue
        b = bino(t)["ai_probability"]
        d = classify(t)
        X.append(features(t, binoculars_prob=b, deberta_ai=d["ai_probability"],
                          deberta_paraphrase=d["paraphrase_probability"]))
        y.append(0 if ex["model"] == "human" else 1)

    base = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
    model = CalibratedClassifierCV(base, method="isotonic", cv=5)
    model.fit(X, y)

    Path("data").mkdir(exist_ok=True)
    joblib.dump(model, "data/stacker.joblib")
    print(f"trained stacker on {len(y)} samples -> data/stacker.joblib")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=3000)
    main(ap.parse_args().sample)
