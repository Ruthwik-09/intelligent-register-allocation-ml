from regalloc import (analyze_liveness, build_cfg, build_interference,
                      parse)
from regalloc.ml import extract_features, train_ranker


def test_features_are_derived_from_program_analysis():
    code = parse("a = x\nb = a + x\nreturn b")
    cfg = build_cfg(code)
    liveness = analyze_liveness(cfg)
    graph = build_interference(cfg, liveness)
    features = extract_features(code, graph, liveness)
    assert features["x"].use_count == 2
    assert features["x"].interference_degree == graph.degree("x")
    assert features["a"].live_range >= 1


def test_model_trains_deterministically_and_ranks_candidates():
    code = parse("low = input\nhot = input\nhot = hot + hot\nreturn hot")
    cfg = build_cfg(code)
    live = analyze_liveness(cfg)
    graph = build_interference(cfg, live)
    feature_set = extract_features(code, graph, live)
    first = train_ranker(feature_set, samples=4096)
    second = train_ranker(feature_set, samples=4096)
    assert first("low", graph) == second("low", graph)
    assert first("hot", graph) > first("low", graph)
