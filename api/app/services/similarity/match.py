"""Turn candidate sources into a similarity report: which passages matched,
which source, and what percentage of the submission is covered."""
from dataclasses import dataclass, asdict
from app.services.similarity.shingle import shingles
from app.core.config import settings

@dataclass
class Match:
    source_id: int
    source_title: str
    start_word: int
    end_word: int
    passage: str

def build_report(text: str, sources: dict[int, tuple[str, set]]) -> dict:
    k = settings.shingle_k
    q = shingles(text)
    words = text.split()
    covered: set[int] = set()
    matches: list[Match] = []

    for sid, (title, sset) in sources.items():
        hit = [i for i, s in enumerate(q) if s in sset]
        if not hit:
            continue
        runs, start, prev = [], hit[0], hit[0]
        for i in hit[1:]:
            if i == prev + 1:
                prev = i
            else:
                runs.append((start, prev)); start = prev = i
        runs.append((start, prev))
        for a, b in runs:
            end = b + k
            covered.update(range(a, end))
            matches.append(Match(sid, title, a, end, " ".join(words[a:end])))

    per_source: dict[int, dict] = {}
    for m in matches:
        s = per_source.setdefault(m.source_id, {"id": m.source_id, "title": m.source_title, "words": 0})
        s["words"] += m.end_word - m.start_word
    total = max(len(words), 1)
    src_list = sorted(per_source.values(), key=lambda s: -s["words"])
    for s in src_list:
        s["percent"] = round(100 * s["words"] / total, 1)

    return {
        "similarity_percent": round(100 * len(covered) / total, 1),
        "word_count": len(words),
        "sources": src_list,
        "matches": [asdict(m) for m in matches],
    }
