"""Fine-tune DeBERTa-v3 on human / ai / ai_paraphrased.

Run scripts/ml/make_dataset.py first. Needs a GPU (free Colab T4 is fine; ~20 min
for a few thousand rows per class). Saves the model to data/ai_classifier/, which
app/services/ai_detect/deberta.py loads at inference time.

    pip install datasets transformers torch scikit-learn accelerate
    python scripts/ml/train_deberta.py
"""
from __future__ import annotations
import numpy as np

BASE = "microsoft/deberta-v3-small"   # -base for better accuracy if you have the GPU time
OUT = "data/ai_classifier"

def main():
    from datasets import load_dataset
    from transformers import (AutoTokenizer, AutoModelForSequenceClassification,
                              Trainer, TrainingArguments, DataCollatorWithPadding)
    from sklearn.metrics import accuracy_score, f1_score

    ds = load_dataset("json", data_files="data/ai_dataset.jsonl")["train"]
    # split by hashing text so near-duplicates don't straddle train/test
    ds = ds.train_test_split(test_size=0.1, seed=42)
    tok = AutoTokenizer.from_pretrained(BASE)

    def tok_fn(b): return tok(b["text"], truncation=True, max_length=512)
    ds = ds.map(tok_fn, batched=True)

    model = AutoModelForSequenceClassification.from_pretrained(BASE, num_labels=3)

    def metrics(p):
        preds = np.argmax(p.predictions, axis=1)
        return {"accuracy": accuracy_score(p.label_ids, preds),
                "macro_f1": f1_score(p.label_ids, preds, average="macro")}

    args = TrainingArguments(
        OUT, num_train_epochs=3, per_device_train_batch_size=16,
        per_device_eval_batch_size=32, learning_rate=2e-5, weight_decay=0.01,
        eval_strategy="epoch", save_strategy="epoch", load_best_model_at_end=True,
        metric_for_best_model="macro_f1", logging_steps=50, report_to=[])
    trainer = Trainer(model=model, args=args, train_dataset=ds["train"],
                      eval_dataset=ds["test"], compute_metrics=metrics,
                      data_collator=DataCollatorWithPadding(tok))
    trainer.train()
    print("eval:", trainer.evaluate())
    model.save_pretrained(OUT); tok.save_pretrained(OUT)
    print(f"saved model to {OUT}/")

if __name__ == "__main__":
    main()
