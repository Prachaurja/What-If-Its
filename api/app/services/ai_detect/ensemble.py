"""Combines detector signals into one calibrated, honest verdict.

Pipeline: Binoculars + DeBERTa -> stacker -> calibrated probability -> band + verdict.
Every stage degrades gracefully: any detector may be missing (not installed / not
trained), and the min-length gate refuses to score very short text. The pure
combination logic below loads no models and is fully unit-tested in CI.
"""
from __future__ import annotations

MIN_WORDS = 150   # below this, detection is unreliable; we say so instead of guessing

def _verdict(prob: float) -> str:
    if prob < 0.30: return "unlikely"
    if prob < 0.60: return "unclear"
    if prob < 0.85: return "likely"
    return "very likely"

def combine(text: str, *, binoculars_prob: float | None = None,
            deberta_ai: float | None = None, paraphrase_prob: float | None = None,
            windows: list | None = None) -> dict:
    """Merge available detector probabilities into a calibrated report fragment."""
    from app.services.ai_detect.stacker import predict as stack

    word_count = len(text.split())
    if word_count < MIN_WORDS:
        return {"scored": False,
                "reason": f"Text is {word_count} words; at least {MIN_WORDS} are needed "
                          "to score reliably.",
                "prob": None, "band": None, "verdict": "not scored",
                "detectors": {"binoculars": binoculars_prob, "deberta": deberta_ai,
                              "paraphrased": paraphrase_prob}}

    available = [p for p in (binoculars_prob, deberta_ai) if p is not None]
    if not available:
        return {"scored": False, "reason": "No detector available.",
                "prob": None, "band": None, "verdict": "not scored", "detectors": {}}

    prob = stack(text, binoculars_prob=binoculars_prob,
                 deberta_ai=deberta_ai, deberta_paraphrase=paraphrase_prob)

    # Band width: base + detector disagreement + short-text penalty.
    disagreement = (max(available) - min(available)) if len(available) > 1 else 0.20
    length_penalty = max(0.0, (300 - word_count) / 300) * 0.10
    half = min(0.25, 0.05 + disagreement / 2 + length_penalty)
    band = [round(max(0.0, prob - half), 3), round(min(1.0, prob + half), 3)]

    result = {
        "scored": True,
        "prob": round(prob, 3),
        "band": band,
        "verdict": _verdict(prob),
        "detectors": {"binoculars": binoculars_prob, "deberta": deberta_ai,
                      "paraphrased": paraphrase_prob},
        "caveat": ("AI-writing signals are probabilistic and can be wrong, "
                   "especially for formulaic or non-native writing. Treat this as a "
                   "prompt for review, not evidence."),
    }
    if paraphrase_prob is not None and paraphrase_prob > 0.5:
        result["note"] = "Signs of AI text that has been paraphrased or 'humanised'."
    if windows:
        result["windows"] = windows
    return result

def run(text: str) -> dict:
    """Full pipeline. Loads whichever detectors are installed/trained."""
    if len(text.split()) < MIN_WORDS:
        return combine(text)

    bino_prob = deberta_ai = paraphrase = None
    windows = None

    try:
        from app.services.ai_detect.binoculars import detect as bino
        bino_prob = bino(text)["ai_probability"]
    except Exception:
        pass

    try:
        from app.services.ai_detect.deberta import classify, is_available
        if is_available():
            d = classify(text)
            deberta_ai = d["ai_probability"]
            paraphrase = d["paraphrase_probability"]
            windows = d["windows"]
    except Exception:
        pass

    return combine(text, binoculars_prob=bino_prob, deberta_ai=deberta_ai,
                   paraphrase_prob=paraphrase, windows=windows)
