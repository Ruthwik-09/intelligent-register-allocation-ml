from regalloc import (analyze_liveness, allocate, build_cfg, build_interference,
                      parse, validate_allocation)


def test_example_runs_through_analysis_and_valid_allocation():
    from pathlib import Path
    source = Path("examples/branching.tac").read_text(encoding="utf-8")
    instructions = parse(source)
    cfg = build_cfg(instructions)
    live = analyze_liveness(cfg)
    graph = build_interference(cfg, live)
    allocation = allocate(graph, ["R1", "R2"])
    assert cfg.entry == 0
    assert any(cfg.blocks[target].label == "loop"
               for block, targets in cfg.successors.items() for target in targets)
    assert validate_allocation(graph, allocation) == []
