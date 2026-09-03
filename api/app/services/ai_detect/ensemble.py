"""Combines detector signals into one calibrated, honest verdict.

Phase 1 ships with Binoculars only. Phase 1b adds the fine-tuned DeBERTa
classifier; `combine()` already accepts its scores so wiring it in later is a
one-line change. The important product logic lives here:

  - min-length gate: refuse to score very short text (high error there)
  - confidence band: widen it when detectors disagree or text is short
  - plain-language verdict buckets

None of this loads a model, so it is fully unit-tested in CI.
"""
from __future__ import annotations

MIN_WORDS = 150   # below this, detection is unreliable; we say so instead of guessing

def _verdict(prob: float) -> str:
    if prob < 0.30: return "unlikely"
    if prob < 0.60: return "unclear"
    if prob < 0.85: return "likely"
    return "very likely"

def combine(text: str, *, binoculars_prob: float | None = None,
            deberta_prob: float | None = None,
            paraphrase_prob: float | None = None) -> dict:
    """Merge available detector probabilities into a calibrated report fragment.

    Any detector may be None (not run / not installed). With only one detector
    the band is wider to reflect lower confidence.
    """
    word_count = len(text.split())
    if word_count < MIN_WORDS:
        return {
            "scored": False,
            "reason": f"Text is {word_count} words; at least {MIN_WORDS} are needed "
                      "to score reliably.",
            "prob": None, "band": None, "verdict": "not scored",
            "detectors": {"binoculars": binoculars_prob, "deberta": deberta_prob,
                          "paraphrased": paraphrase_prob},
        }

    probs = [p for p in (binoculars_prob, deberta_prob) if p is not None]
    if not probs:
        return {"scored": False, "reason": "No detector available.",
                "prob": None, "band": None, "verdict": "not scored",
                "detectors": {}}

    # Weighted mean (equal weights for now; the stacker in Phase 1b learns these).
    prob = sum(probs) / len(probs)

    # Band width: base uncertainty + disagreement between detectors + short-text penalty.
    disagreement = (max(probs) - min(probs)) if len(probs) > 1 else 0.20
    length_penalty = max(0.0, (300 - word_count) / 300) * 0.10
    half = min(0.25, 0.05 + disagreement / 2 + length_penalty)
    band = [round(max(0.0, prob - half), 3), round(min(1.0, prob + half), 3)]

    result = {
        "scored": True,
        "prob": round(prob, 3),
        "band": band,
        "verdict": _verdict(prob),
        "detectors": {"binoculars": binoculars_prob, "deberta": deberta_prob,
                      "paraphrased": paraphrase_prob},
        "caveat": ("AI-writing signals are probabilistic and can be wrong, "
                   "especially for formulaic or non-native writing. Treat this as a "
                   "prompt for review, not evidence."),
    }
    return result

def run(text: str) -> dict:
    """Full pipeline: load Binoculars, score, combine. Used by the worker/report.
    Kept thin so the heavy import only happens when actually scoring.
    """
    if len(text.split()) < MIN_WORDS:
        return combine(text)
    from app.services.ai_detect.binoculars import detect as bino
    b = bino(text)
    return combine(text, binoculars_prob=b["ai_probability"])
