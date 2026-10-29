from regalloc import (InterferenceGraph, allocate, validate_allocation)


def test_coloring_never_assigns_same_register_to_interfering_values():
    graph = InterferenceGraph({
        "a": frozenset({"b"}),
        "b": frozenset({"a", "c"}),
        "c": frozenset({"b"}),
    })
    allocation = allocate(graph, ["R1", "R2"])
    assert allocation.spills == {}
    assert not validate_allocation(graph, allocation)
    assert allocation.registers["a"] != allocation.registers["b"]
    assert allocation.registers["b"] != allocation.registers["c"]


def test_clique_spills_when_registers_are_insufficient():
    graph = InterferenceGraph({
        "a": frozenset({"b", "c"}),
        "b": frozenset({"a", "c"}),
        "c": frozenset({"a", "b"}),
    })
    allocation = allocate(graph, ["R1", "R2"])
    assert len(allocation.spills) == 1
    assert len(allocation.registers) == 2
    assert not validate_allocation(graph, allocation)


def test_custom_spill_cost_selects_lower_cost_candidate_in_clique():
    graph = InterferenceGraph({"a": frozenset({"b"}), "b": frozenset({"a"})})
    allocation = allocate(graph, ["R1"], spill_score=lambda v, _g: 0 if v == "a" else 9)
    assert allocation.spills == {"a": 0}
    assert not validate_allocation(graph, allocation)


def test_validator_reports_invalid_manual_coloring():
    graph = InterferenceGraph({"a": frozenset({"b"}), "b": frozenset({"a"})})
    from regalloc import Allocation
    invalid = Allocation({"a": "R1", "b": "R1"}, {}, 1)
    assert any("share R1" in error for error in validate_allocation(graph, invalid))
