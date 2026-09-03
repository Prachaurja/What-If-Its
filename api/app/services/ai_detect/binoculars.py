"""Binoculars — zero-shot AI-text detection (Hans et al., 2024).

The intuition: a language model finds AI-generated text *unusually* unsurprising.
But some human text is unsurprising too (recipes, boilerplate), so raw perplexity
gives false positives. Binoculars divides by a second quantity that measures how
predictable the text is *in general*, cancelling the "boring topic" effect.

Two models that share a tokenizer:
  observer  — a base model (e.g. Falcon-7B)
  performer — its instruct-tuned sibling (e.g. Falcon-7B-instruct)

  perplexity        = how surprised the observer is by the actual text
  cross_perplexity  = how surprised the observer is by the performer's predictions
  binoculars score  = perplexity / cross_perplexity

Human text scores high (~1.0+); machine text scores low (below a calibrated
threshold, ~0.9). Lower = more likely machine.

The two 7B models need a GPU or ~16 GB RAM (8-bit). For local dev / CI you can
point this at a tiny model pair via env vars; the math is identical.
"""
from __future__ import annotations
import os
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForCausalLM

OBSERVER = os.getenv("BINOCULARS_OBSERVER", "tiiuae/falcon-7b")
PERFORMER = os.getenv("BINOCULARS_PERFORMER", "tiiuae/falcon-7b-instruct")

# Threshold from the paper, tuned for low false-positive rate. Recalibrate on
# your own validation set with scripts/ml/calibrate_binoculars.py.
DEFAULT_THRESHOLD = float(os.getenv("BINOCULARS_THRESHOLD", "0.901"))

_tok = _obs = _perf = None

def _load():
    global _tok, _obs, _perf
    if _obs is None:
        _tok = AutoTokenizer.from_pretrained(OBSERVER)
        if _tok.pad_token is None:
            _tok.pad_token = _tok.eos_token
        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        _obs = AutoModelForCausalLM.from_pretrained(OBSERVER, torch_dtype=dtype).eval()
        _perf = AutoModelForCausalLM.from_pretrained(PERFORMER, torch_dtype=dtype).eval()

@torch.no_grad()
def _perplexity(logits, input_ids, attention_mask):
    """Mean token-level cross-entropy of the text under `logits` (observer)."""
    shift_logits = logits[..., :-1, :].contiguous()
    shift_labels = input_ids[..., 1:].contiguous()
    shift_mask = attention_mask[..., 1:].contiguous()
    ce = F.cross_entropy(shift_logits.transpose(1, 2), shift_labels, reduction="none")
    return (ce * shift_mask).sum(1) / shift_mask.sum(1)

@torch.no_grad()
def _cross_perplexity(obs_logits, perf_logits, attention_mask):
    """How surprised the observer is by the performer's next-token distribution.
    = sum over vocab of softmax(performer) * -log_softmax(observer), per position.
    """
    p = F.softmax(perf_logits[..., :-1, :], dim=-1)
    logq = F.log_softmax(obs_logits[..., :-1, :], dim=-1)
    x = (-p * logq).sum(-1)                       # per-position cross entropy
    mask = attention_mask[..., 1:].contiguous()
    return (x * mask).sum(1) / mask.sum(1)

@torch.no_grad()
def binoculars_score(text: str) -> float:
    """Return the raw Binoculars ratio. Lower = more likely machine-generated."""
    _load()
    enc = _tok(text, return_tensors="pt", truncation=True, max_length=512,
               return_token_type_ids=False)
    obs_out = _obs(**enc).logits
    perf_out = _perf(**enc).logits
    ppl = _perplexity(obs_out, enc["input_ids"], enc["attention_mask"])
    x_ppl = _cross_perplexity(obs_out, perf_out, enc["attention_mask"])
    return (ppl / x_ppl).item()

def score_to_probability(score: float, threshold: float = DEFAULT_THRESHOLD,
                         steepness: float = 12.0) -> float:
    """Map the raw ratio to P(AI) in [0,1]. Score below threshold -> >0.5.
    Steepness is a soft slope; replace with a fitted calibrator for real use.
    """
    import math
    return 1.0 / (1.0 + math.exp(steepness * (score - threshold)))

def detect(text: str, threshold: float = DEFAULT_THRESHOLD) -> dict:
    score = binoculars_score(text)
    return {
        "detector": "binoculars",
        "score": round(score, 4),
        "threshold": threshold,
        "ai_probability": round(score_to_probability(score, threshold), 4),
        "verdict": "ai" if score < threshold else "human",
    }
