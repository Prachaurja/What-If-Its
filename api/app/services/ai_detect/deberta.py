"""Supervised AI-text classifier — the second half of the ensemble.

Where Binoculars measures a *property* of the text (predictability) and so
generalises to unseen models, DeBERTa learns the *style* of AI writing from
labelled examples. That makes it the tool for the case Binoculars is weakest on:
paraphrased / "humanised" AI text, which is deliberately made less predictable
but still carries the tell-tale word-choice and rhythm a classifier can learn.

Three classes:
    0 human
    1 ai
    2 ai_paraphrased   (AI text run through a humaniser/paraphraser)

Train it with scripts/ml/train_deberta.py, which writes the model to
data/ai_classifier/. Inference here loads that folder. Runs on CPU in
milliseconds — no GPU needed at serve time (only for training).

Sentence/window scores let the UI highlight *which* parts look generated:
the document is split into ~300-token windows and each is scored.
"""
from __future__ import annotations
import os
from pathlib import Path

MODEL_DIR = Path(os.getenv("DEBERTA_DIR", "data/ai_classifier"))
LABELS = ["human", "ai", "ai_paraphrased"]

_tok = _model = None

def is_available() -> bool:
    """True only if a trained model exists on disk. Lets the ensemble skip
    DeBERTa cleanly until you've trained one."""
    return (MODEL_DIR / "config.json").exists()

def _load():
    global _tok, _model
    if _model is None:
        import torch  # noqa
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        _tok = AutoTokenizer.from_pretrained(str(MODEL_DIR))
        _model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_DIR)).eval()

def _windows(text: str, size_tokens: int = 300, overlap: int = 50) -> list[str]:
    """Split into overlapping word windows (~token proxy) for per-region scoring."""
    words = text.split()
    if len(words) <= size_tokens:
        return [text]
    step = size_tokens - overlap
    return [" ".join(words[i:i + size_tokens]) for i in range(0, len(words), step)]

def classify(text: str) -> dict:
    """Return class probabilities for the whole document plus per-window scores."""
    import torch
    _load()
    windows = _windows(text)
    enc = _tok(windows, return_tensors="pt", truncation=True, max_length=512, padding=True)
    with torch.no_grad():
        probs = _model(**enc).logits.softmax(-1)          # [n_windows, 3]
    doc = probs.mean(0).tolist()                          # average across windows
    per_window = [
        {"text": w[:120], "human": round(p[0].item(), 3),
         "ai": round(p[1].item(), 3), "ai_paraphrased": round(p[2].item(), 3)}
        for w, p in zip(windows, probs)
    ]
    return {
        "detector": "deberta",
        "probs": {lbl: round(v, 3) for lbl, v in zip(LABELS, doc)},
        # single "AI-involved" number = P(ai) + P(ai_paraphrased)
        "ai_probability": round(doc[1] + doc[2], 3),
        "paraphrase_probability": round(doc[2], 3),
        "windows": per_window,
    }
