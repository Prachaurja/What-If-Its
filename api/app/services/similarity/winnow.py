"""Winnowing: keep only the minimum hash in each sliding window of w hashes.

This shrinks the index ~5x while guaranteeing any copied run of at least
(k + w - 1) words shares a fingerprint with its source. Same idea MOSS uses.
"""
import hashlib
from app.core.config import settings

def h(shingle: str) -> int:
    # 63-bit so it fits a signed BIGINT column in Postgres.
    return int(hashlib.blake2b(shingle.encode(), digest_size=8).hexdigest(), 16) >> 1

def fingerprints(shingle_list: list[str], w: int | None = None) -> list[tuple[int, int]]:
    """Return (hash, position) pairs after winnowing."""
    w = w or settings.winnow_w
    hashes = [h(s) for s in shingle_list]
    if len(hashes) < w:
        # too short to winnow — keep all, they're few
        return list({(hv, i) for i, hv in enumerate(hashes)})
    out, last = [], None
    for i in range(len(hashes) - w + 1):
        window = hashes[i:i + w]
        m = min(window)
        pos = i + window.index(m)
        if (m, pos) != last:
            out.append((m, pos)); last = (m, pos)
    return out
