"""Typed intermediate representation for the supported TAC subset."""

from dataclasses import dataclass
from typing import TypeAlias


@dataclass(frozen=True)
class Operand:
    """A variable name or integer literal."""

    value: str | int

    @property
    def is_variable(self) -> bool:
        return isinstance(self.value, str)


@dataclass(frozen=True)
class Assign:
    dest: str
    value: Operand
    line: int


@dataclass(frozen=True)
class BinaryOp:
    dest: str
    left: Operand
    operator: str
    right: Operand
    line: int


@dataclass(frozen=True)
class Label:
    name: str
    line: int


@dataclass(frozen=True)
class Goto:
    target: str
    line: int


@dataclass(frozen=True)
class IfGoto:
    """Conditional branch; right is absent for a truthy-variable test."""

    left: Operand
    operator: str
    right: Operand | None
    target: str
    line: int


@dataclass(frozen=True)
class Return:
    value: Operand | None
    line: int


Instruction: TypeAlias = Assign | BinaryOp | Label | Goto | IfGoto | Return
