"""Parser for a documented, deliberately small three-address-code language."""

import re

from .ir import Assign, BinaryOp, Goto, IfGoto, Instruction, Label, Operand, Return

_IDENT = r"[A-Za-z_][A-Za-z0-9_]*"
_OPERAND = rf"(?:{_IDENT}|-?\d+)"
_BIN_OPS = {"+", "-", "*", "/", "%"}
_REL_OPS = {"==", "!=", "<", "<=", ">", ">="}
_REL_PATTERN = r"==|!=|<=|>=|<|>"


class ParseError(ValueError):
    """A source error with its source line and a useful diagnostic."""

    def __init__(self, line: int, message: str):
        self.line = line
        self.message = message
        super().__init__(f"line {line}: {message}")


def _operand(token: str) -> Operand:
    return Operand(int(token)) if re.fullmatch(r"-?\d+", token) else Operand(token)


def parse(source: str) -> list[Instruction]:
    """Parse TAC and reject malformed instructions, duplicate or missing labels.

    Supported statements: ``x = y``, ``x = y op z`` (arithmetic operators
    + - * / %), ``goto L``, ``if x goto L``, ``if x relop y goto L``,
    ``return`` / ``return x``, and a label ``L:``. A label may prefix one
    statement (``L: x = 1``). Identifiers follow Python-like ASCII identifier
    syntax; operands are identifiers or signed decimal integers. Blank lines
    and text after ``#`` are ignored. There are no calls, arrays, unary ops,
    strings, or implicit declarations. Every branch target must be defined.
    """
    instructions: list[Instruction] = []
    labels: dict[str, int] = {}
    targets: list[tuple[str, int]] = []

    for line_no, raw in enumerate(source.splitlines(), 1):
        text = raw.split("#", 1)[0].strip()
        if not text:
            continue

        label_match = re.match(rf"^({_IDENT}):(?:\s*(.*))?$", text)
        if label_match:
            name, remainder = label_match.group(1), (label_match.group(2) or "").strip()
            if name in labels:
                raise ParseError(line_no, f"duplicate label '{name}'")
            labels[name] = line_no
            instructions.append(Label(name, line_no))
            text = remainder
            if not text:
                continue

        match = re.fullmatch(rf"goto\s+({_IDENT})", text)
        if match:
            target = match.group(1)
            instructions.append(Goto(target, line_no))
            targets.append((target, line_no))
            continue

        match = re.fullmatch(rf"if\s+({_OPERAND})\s+({_REL_PATTERN})\s+({_OPERAND})\s+goto\s+({_IDENT})", text)
        if match:
            left, op, right, target = match.groups()
            instructions.append(IfGoto(_operand(left), op, _operand(right), target, line_no))
            targets.append((target, line_no))
            continue

        match = re.fullmatch(rf"if\s+({_IDENT})\s+goto\s+({_IDENT})", text)
        if match:
            var, target = match.groups()
            instructions.append(IfGoto(Operand(var), "!=", Operand(0), target, line_no))
            targets.append((target, line_no))
            continue

        if text == "return":
            instructions.append(Return(None, line_no))
            continue
        match = re.fullmatch(rf"return\s+({_OPERAND})", text)
        if match:
            instructions.append(Return(_operand(match.group(1)), line_no))
            continue

        match = re.fullmatch(rf"({_IDENT})\s*=\s*({_OPERAND})", text)
        if match:
            dest, value = match.groups()
            instructions.append(Assign(dest, _operand(value), line_no))
            continue

        match = re.fullmatch(rf"({_IDENT})\s*=\s*({_OPERAND})\s*([^\s]+)\s*({_OPERAND})", text)
        if match:
            dest, left, op, right = match.groups()
            if op in _BIN_OPS:
                instructions.append(BinaryOp(dest, _operand(left), op, _operand(right), line_no))
            else:
                raise ParseError(line_no, f"unsupported operator '{op}'")
            continue

        if re.match(r"^(call|print|read|switch|function|param)\b", text):
            keyword = text.split(None, 1)[0]
            raise ParseError(line_no, f"unsupported instruction '{keyword}'")
        raise ParseError(line_no, f"invalid or unsupported syntax: {text!r}")

    for target, line_no in targets:
        if target not in labels:
            raise ParseError(line_no, f"undefined label '{target}'")
    return instructions
