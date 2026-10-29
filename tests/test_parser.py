import pytest

from regalloc import Assign, BinaryOp, Goto, IfGoto, Label, Operand, ParseError, Return, parse


def test_parses_supported_instruction_types():
    result = parse("""a = source
b = a + 12
if b >= 3 goto done
goto done
done:
return b
""")
    assert result == [
        Assign("a", Operand("source"), 1),
        BinaryOp("b", Operand("a"), "+", Operand(12), 2),
        IfGoto(Operand("b"), ">=", Operand(3), "done", 3),
        Goto("done", 4),
        Label("done", 5),
        Return(Operand("b"), 6),
    ]


def test_parses_truthy_branch_and_inline_label():
    result = parse("if flag goto yes\nyes: answer = -4\nreturn")
    assert result[0] == IfGoto(Operand("flag"), "!=", Operand(0), "yes", 1)
    assert result[1] == Label("yes", 2)
    assert result[2] == Assign("answer", Operand(-4), 2)
    assert result[3] == Return(None, 3)


def test_ignores_blank_lines_and_hash_comments():
    assert parse("\n# comment\nx = 1 # trailing comment\n") == [Assign("x", Operand(1), 3)]


@pytest.mark.parametrize("source", ["x =", "x = a +", "if x goto", "x = 2 ** 3"])
def test_rejects_malformed_or_unsupported_syntax(source):
    with pytest.raises(ParseError, match="line 1:"):
        parse(source)


@pytest.mark.parametrize("source, message", [
    ("call foo", "unsupported instruction 'call'"),
    ("print x", "unsupported instruction 'print'"),
])
def test_names_unsupported_instructions(source, message):
    with pytest.raises(ParseError, match=message):
        parse(source)


def test_rejects_undefined_branch_targets():
    with pytest.raises(ParseError, match="undefined label 'missing'"):
        parse("goto missing")


def test_rejects_duplicate_labels():
    with pytest.raises(ParseError, match="duplicate label 'loop'"):
        parse("loop:\nloop:")
