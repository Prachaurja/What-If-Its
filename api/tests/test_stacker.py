from app.services.ai_detect.stacker import predict, features

LONG = " ".join(["The council reviewed the proposal carefully."] * 40)

def test_fallback_blends_detectors():
    # with both detectors, fallback returns something between them
    p = predict(LONG, binoculars_prob=0.9, deberta_ai=0.7, deberta_paraphrase=0.0)
    assert 0.6 <= p <= 0.95

def test_paraphrase_shifts_weight_to_deberta():
    # DeBERTa says AI (0.9), Binoculars says human (0.2). With high paraphrase
    # signal, the blend should lean toward DeBERTa's higher value.
    no_para = predict(LONG, binoculars_prob=0.2, deberta_ai=0.9, deberta_paraphrase=0.0)
    with_para = predict(LONG, binoculars_prob=0.2, deberta_ai=0.9, deberta_paraphrase=0.9)
    assert with_para > no_para

def test_features_length_and_ttr():
    f = features(LONG, binoculars_prob=0.5, deberta_ai=0.5, deberta_paraphrase=0.0)
    assert len(f) == 6
    assert 0.0 <= f[5] <= 1.0     # type-token ratio in range

def test_single_detector_passthrough():
    assert predict(LONG, binoculars_prob=0.77, deberta_ai=None, deberta_paraphrase=None) == 0.77
