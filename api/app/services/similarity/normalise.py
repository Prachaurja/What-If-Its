"""Lowercase, strip punctuation, split into tokens. Trivial edits (caps,
punctuation) shouldn't let copied text slip past."""
import re

def normalise(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return text.split()
