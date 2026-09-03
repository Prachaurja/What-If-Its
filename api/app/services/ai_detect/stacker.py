"""The stacker: turns raw detector outputs into one calibrated probability.

Averaging Binoculars and DeBERTa is crude — it trusts both equally everywhere.
A stacker is a tiny logistic-regression model trained on a held-out set that
learns *when* to trust each detector (e.g. lean on DeBERTa when it flags
paraphrasing, lean on Binoculars on long text). Isotonic calibration then makes
the output honest: a reported 0.80 means AI-involved 80% of the time.

Trained by scripts/ml/train_stacker.py, saved to data/stacker.joblib.
If no trained stacker exists, `predict()` falls back to a transparent weighted
blend so the ensemble still works before training.

Feature vector (all cheap, no model calls beyond the detectors themselves):
    binoculars_prob, deberta_ai, deberta_paraphrase,
    word_count_norm, mean_sentence_len_norm, type_token_ratio
"""
from __future__ import annotations
import os, re
from pathlib import Path

STACKER_PATH = Path(os.getenv("STACKER_PATH", "data/stacker.joblib"))

def features(text: str, *, binoculars_prob: float | None,
             deberta_ai: float | None, deberta_paraphrase: float | None) -> list[float]:
    words = text.split()
    wc = len(words)
    sents = [s for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    mean_sent = (wc / len(sents)) if sents else wc
    ttr = (len(set(w.lower() for w in words)) / wc) if wc else 0.0
    return [
        binoculars_prob if binoculars_prob is not None else 0.5,
        deberta_ai if deberta_ai is not None else 0.5,
        deberta_paraphrase if deberta_paraphrase is not None else 0.0,
        min(wc / 1000.0, 1.0),          # word count, normalised & capped
        min(mean_sent / 40.0, 1.0),     # mean sentence length, normalised
        ttr,                            # lexical diversity
    ]

def is_trained() -> bool:
    return STACKER_PATH.exists()

def predict(text: str, *, binoculars_prob: float | None,
            deberta_ai: float | None, deberta_paraphrase: float | None) -> float:
    """Return calibrated P(AI-involved). Uses the trained stacker if present,
    else a transparent weighted fallback."""
    x = features(text, binoculars_prob=binoculars_prob,
                 deberta_ai=deberta_ai, deberta_paraphrase=deberta_paraphrase)
    if is_trained():
        import joblib
        model = joblib.load(STACKER_PATH)          # sklearn Pipeline w/ calibration
        return float(model.predict_proba([x])[0][1])

    # Fallback: weighted blend. DeBERTa is weighted up when it detects
    # paraphrasing (the case Binoculars misses); Binoculars carries long text.
    b = binoculars_prob if binoculars_prob is not None else None
    d = deberta_ai if deberta_ai is not None else None
    if b is None and d is None:
        return 0.5
    if b is None:
        return d
    if d is None:
        return b
    para = deberta_paraphrase or 0.0
    w_d = 0.5 + 0.3 * para                          # trust DeBERTa more if paraphrase suspected
    w_d = min(w_d, 0.8)
    return round(w_d * d + (1 - w_d) * b, 4)
