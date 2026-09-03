"""Build the 3-class training set: human / ai / ai_paraphrased.

The paraphrased class is what makes Swipe catch "humanised" AI text — you can't
learn it without examples of it, so we manufacture them: take AI text and run it
through a paraphraser (a stand-in for QuillBot / Undetectable.ai).

Sources:
  human, ai  -> HC3 (Hello-SimpleAI/HC3) + RAID human/model splits
  paraphrase -> the 'ai' rows pushed through a T5 paraphrase model (free, local)

Writes data/ai_dataset.jsonl with {text, label}. Run on Colab (GPU speeds up the
paraphraser a lot). Scale n_per_class up once the pipeline works.

    pip install datasets transformers torch
    python scripts/ml/make_dataset.py --n 3000
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

def main(n: int):
    from datasets import load_dataset
    from transformers import pipeline

    Path("data").mkdir(exist_ok=True)
    out = Path("data/ai_dataset.jsonl")
    rows = []

    # --- human + ai from HC3 ---
    hc3 = load_dataset("Hello-SimpleAI/HC3", "all", split="train").shuffle(seed=42)
    para = pipeline("text2text-generation",
                    model="humarin/chatgpt_paraphraser_on_T5_base", max_length=256)

    made = {"human": 0, "ai": 0, "para": 0}
    for ex in hc3:
        if made["human"] < n and ex["human_answers"]:
            h = ex["human_answers"][0]
            if len(h.split()) > 40:
                rows.append({"text": h, "label": 0}); made["human"] += 1
        if made["ai"] < n and ex["chatgpt_answers"]:
            a = ex["chatgpt_answers"][0]
            if len(a.split()) > 40:
                rows.append({"text": a, "label": 1}); made["ai"] += 1
                if made["para"] < n:
                    p = para(a[:900])[0]["generated_text"]
                    rows.append({"text": p, "label": 2}); made["para"] += 1
        if all(v >= n for v in made.values()):
            break

    with out.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"wrote {len(rows)} rows to {out}: {made}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3000, help="target rows per class")
    main(ap.parse_args().n)
