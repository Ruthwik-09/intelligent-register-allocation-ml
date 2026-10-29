from regalloc import analyze_liveness, build_cfg, build_interference, parse


def test_iterative_liveness_handles_loop_backedge():
    cfg = build_cfg(parse("loop:\ny = x + 1\nif y < 10 goto loop\nreturn y"))
    result = analyze_liveness(cfg)
    assert result.live_in[0] == frozenset({"x"})
    assert result.live_out[0] == frozenset({"x", "y"})
    assert result.live_in[1] == frozenset({"y"})
    assert result.live_out[1] == frozenset()


def test_interference_matches_simultaneously_live_values():
    cfg = build_cfg(parse("a = x\nb = y\nc = a + b\nreturn c"))
    graph = build_interference(cfg, analyze_liveness(cfg))
    assert "b" in graph.neighbors["a"]
    assert "a" not in graph.neighbors["c"]
    assert graph.variables == frozenset({"a", "b", "c", "x", "y"})


def test_dead_assignment_destinations_still_exist_as_nodes():
    cfg = build_cfg(parse("unused = 9\nreturn"))
    graph = build_interference(cfg, analyze_liveness(cfg))
    assert "unused" in graph.variables
