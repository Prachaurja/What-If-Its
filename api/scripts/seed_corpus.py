"""Load every file in ../corpus into the database as reference sources."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from app.db.session import SessionLocal
from app.services.extract import extract_text
from app.services.similarity.index import add_document
from app.models.document import DocKind

CORPUS = pathlib.Path(__file__).resolve().parents[2] / "corpus"

def main():
    if not CORPUS.exists():
        print("no corpus/ directory"); return
    with SessionLocal() as db:
        for p in sorted(CORPUS.iterdir()):
            if p.suffix.lower() in (".txt", ".md", ".docx", ".pdf"):
                doc = add_document(db, p.name, extract_text(p.name, p.read_bytes()), DocKind.source)
                print(f"indexed {p.name} ({doc.word_count} words)")

if __name__ == "__main__":
    main()
