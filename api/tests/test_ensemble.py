from app.services.ai_detect.ensemble import combine, MIN_WORDS

LONG = " ".join(["word"] * 200)

def test_short_text_not_scored():
    r = combine("only a few words here", binoculars_prob=0.9)
    assert r["scored"] is False
    assert "150" in r["reason"]

def test_single_detector_scores_with_wide_band():
    r = combine(LONG, binoculars_prob=0.8)
    assert r["scored"] is True
    assert r["prob"] == 0.8
    lo, hi = r["band"]
    assert lo < 0.8 < hi
    assert hi - lo > 0.1          # single detector => wide band

def test_agreeing_detectors_narrow_band():
    r = combine(LONG, binoculars_prob=0.82, deberta_prob=0.80)
    wide = combine(LONG, binoculars_prob=0.82, deberta_prob=0.20)
    assert (r["band"][1] - r["band"][0]) < (wide["band"][1] - wide["band"][0])

def test_verdict_buckets():
    assert combine(LONG, binoculars_prob=0.1)["verdict"] == "unlikely"
    assert combine(LONG, binoculars_prob=0.5)["verdict"] == "unclear"
    assert combine(LONG, binoculars_prob=0.75)["verdict"] == "likely"
    assert combine(LONG, binoculars_prob=0.95)["verdict"] == "very likely"

def test_no_detector_available():
    assert combine(LONG)["scored"] is False
