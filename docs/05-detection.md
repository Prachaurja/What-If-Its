# 05 · Detection engines

## 5.1 Similarity

```
text ─▶ normalise ─▶ shingle (k=5 words) ─▶ hash (blake2b, 63-bit)
     ─▶ winnow (w=8) ─▶ fingerprints ─▶ candidate lookup (Postgres GROUP BY)
     ─▶ exact rescoring on candidates (full shingle sets)
     ─▶ merge hits into passages ─▶ mark quoted/reference passages
     ─▶ per-source %, document %
```

- **Winnowing** guarantees any copied run of ≥ k+w−1 = 12 words is caught, at ~22% of the storage of full shingling.
- **Exclusions** run before scoring: quoted spans (matching quote pairs, block quotes) and everything after a `References`/`Bibliography`/`Works Cited` heading are matched but flagged `quoted`, and not counted when the option is set.
- **Repositories** a check compares against: the org's own documents (submissions + sources), the shared public corpus (`org_id NULL`, kind=source), and the web cache (kind=web). Never another org's documents.
- **Same-author resubmission**: if `text_hash` matches a prior submission by the same user, report says so and excludes it.

Corpus ingestion order: Wikipedia (2.5B words) → arXiv abstracts + full text → Project Gutenberg → Semantic Scholar open access → CC-News. Each via a streaming script with COPY.

## 5.2 Web fallback

```
unmatched sentences ─▶ rank by distinctiveness (IDF sum, length, proper nouns)
  ─▶ top 12 ─▶ exact-phrase search (Brave API, 24 h cache)
  ─▶ dedupe URLs ─▶ fetch + clean (trafilatura, 5 s timeout, 2 MB cap)
  ─▶ fingerprint on the fly ─▶ same matcher ─▶ cache page as kind=web
```

Budget: ≤ 12 queries and ≤ 30 fetches per check, ~$0.06. Skipped on free plan.

## 5.3 AI-writing ensemble

```
text ─▶ min-length gate (≥150 words, else scored=false + reason)
     ├─▶ Binoculars   (Falcon-7B observer / Falcon-7B-instruct performer, 4-bit)  → score
     ├─▶ DeBERTa-v3   (3-class: human / ai / ai_paraphrased, 300-token windows)  → p_ai, p_para, per-window
     └─▶ features     (word count, mean sentence length, TTR, burstiness)
             ▼
        stacker (logistic regression) ─▶ isotonic calibration ─▶ prob
        band width = f(detector disagreement, length)
        verdict: unlikely (<0.3) · unclear (0.3–0.6) · likely (0.6–0.85) · very likely (>0.85)
```

Sentence highlights come from DeBERTa windows; the document number from the stacker.

### Training data

| Class | Sources |
|---|---|
| human | RAID human split, PERSUADE student essays, Wikipedia, Reddit, OpenWebText |
| ai | RAID (11 models); own generations from 6+ current models using the *same prompts* as the human essays |
| ai_paraphrased | ai class through T5 paraphraser + LLM "rewrite to sound human" prompts + RAID adversarial split |

~50k windows per class. Held-out validation split by *prompt*, not by sample, so topic leakage can't inflate scores.

### Evaluation (published in the app's docs)

Per-model and per-domain: accuracy, false-positive rate on human text, FPR on ESL essays specifically, AUROC. Target: ≥ 92% accuracy on RAID held-out, ≤ 2% FPR on PERSUADE human essays.

### What the UI must always say

- The band, not just the number.
- "Not scored — under 150 words" when applicable.
- "AI-writing signals are probabilistic; treat as a prompt for review, not evidence."
