from app.services.ai_detect.ensemble import combine, MIN_WORDS

LONG = " ".join(["word"] * 200)

def test_short_text_not_scored():
    r = combine("only a few words here", binoculars_prob=0.9)
    assert r["scored"] is False
    assert "150" in r["reason"]

def test_single_detector_scores_with_wide_band():
    r = combine(LONG, binoculars_prob=0.8)
    assert r["scored"] is True
    lo, hi = r["band"]
    assert lo < r["prob"] < hi
    assert hi - lo > 0.1          # single detector => wide band

def test_agreeing_detectors_narrow_band():
    agree = combine(LONG, binoculars_prob=0.82, deberta_ai=0.80)
    disagree = combine(LONG, binoculars_prob=0.82, deberta_ai=0.20)
    assert (agree["band"][1] - agree["band"][0]) < (disagree["band"][1] - disagree["band"][0])

def test_verdict_buckets():
    assert combine(LONG, binoculars_prob=0.1)["verdict"] == "unlikely"
    assert combine(LONG, binoculars_prob=0.5)["verdict"] == "unclear"
    assert combine(LONG, binoculars_prob=0.75)["verdict"] == "likely"
    assert combine(LONG, binoculars_prob=0.95)["verdict"] == "very likely"

def test_paraphrase_note_surfaces():
    r = combine(LONG, binoculars_prob=0.4, deberta_ai=0.8, paraphrase_prob=0.7)
    assert "note" in r and "paraphrased" in r["note"]

def test_no_detector_available():
    assert combine(LONG)["scored"] is False
