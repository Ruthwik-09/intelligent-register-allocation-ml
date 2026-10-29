import pytest

from regalloc import IfGoto, Return, build_cfg, parse


def test_builds_blocks_and_branch_edges():
    source = "entry:\nx = 1\nif x < 2 goto yes\nx = 3\ngoto done\nyes:\nx = 4\ndone:\nreturn x"
    cfg = build_cfg(parse(source))
    assert [block.label for block in cfg.blocks] == ["entry", None, "yes", "done"]
    assert cfg.successors == {
        0: frozenset({1, 2}),
        1: frozenset({3}),
        2: frozenset({3}),
        3: frozenset(),
    }
    assert cfg.predecessors[3] == frozenset({1, 2})


def test_goto_has_no_fallthrough_and_return_ends_flow():
    cfg = build_cfg(parse("goto end\nx = 1\nend:\nreturn"))
    assert cfg.successors[0] == frozenset({2})
    assert cfg.successors[1] == frozenset({2})
    assert isinstance(cfg.blocks[2].instructions[-1], Return)
    assert cfg.successors[2] == frozenset()


def test_empty_program_has_no_entry():
    cfg = build_cfg(parse("# empty"))
    assert cfg.blocks == ()
    assert cfg.entry is None


def test_cfg_checks_targets_for_hand_built_ir():
    from regalloc import Operand
    with pytest.raises(ValueError, match="undefined label 'lost'"):
        build_cfg([IfGoto(Operand("x"), "!=", Operand(0), "lost", 1)])
