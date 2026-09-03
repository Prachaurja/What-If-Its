"""Overlapping word n-grams. 'the cat sat on the mat' (k=3) ->
'the cat sat', 'cat sat on', ... Copying one sentence leaves several
identical shingles behind."""
from app.services.similarity.normalise import normalise
from app.core.config import settings

def shingles(text: str, k: int | None = None) -> list[str]:
    k = k or settings.shingle_k
    toks = normalise(text)
    if len(toks) < k:
        return [" ".join(toks)] if toks else []
    return [" ".join(toks[i:i + k]) for i in range(len(toks) - k + 1)]
