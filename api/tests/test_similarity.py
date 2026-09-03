from app.services.similarity.index import add_document, candidates
from app.services.similarity.match import build_report
from app.services.similarity.winnow import fingerprints
from app.services.similarity.shingle import shingles
from app.models.document import DocKind

# Winnowing only retains fingerprints once text is longer than the window
# (k + w - 1 words), so tests use realistic passage lengths, not toy strings.

SRC = ("Photosynthesis is a system of biological processes by which photosynthetic "
       "organisms convert light energy typically from sunlight into the chemical energy "
       "necessary to fuel their metabolism. The process usually takes place in chloroplasts "
       "and uses carbon dioxide and water to produce glucose and oxygen as a byproduct.")

def test_winnow_catches_long_copied_run():
    fp_src = {h for h, _ in fingerprints(shingles(SRC))}
    copy = "As noted, " + SRC + " That concludes the point."
    fp_copy = {h for h, _ in fingerprints(shingles(copy))}
    assert len(fp_src & fp_copy) >= 3

def test_copied_passage_detected(db):
    add_document(db, "wiki", SRC, DocKind.source)
    q = ("In this essay I explain that photosynthesis is a system of biological processes "
         "by which photosynthetic organisms convert light energy typically from sunlight "
         "into the chemical energy necessary to fuel their metabolism, which matters greatly.")
    r = build_report(q, candidates(db, q))
    assert r["similarity_percent"] > 30
    assert r["sources"][0]["title"] == "wiki"

def test_original_is_clean(db):
    add_document(db, "wiki", SRC, DocKind.source)
    q = ("Data science students in Melbourne enjoy strong flat whites and long tram rides "
         "home along the Yarra, chatting about football and weekend plans with their friends.")
    assert build_report(q, candidates(db, q))["similarity_percent"] == 0
