"""Educational register allocation compiler components."""

from .ir import (
    Assign,
    BinaryOp,
    Goto,
    IfGoto,
    Instruction,
    Label,
    Operand,
    Return,
)
from .parser import ParseError, parse
from .cfg import BasicBlock, ControlFlowGraph, build_cfg
from .liveness import LivenessResult, analyze_liveness, uses_defs
from .interference import InterferenceGraph, build_interference
from .allocator import Allocation, allocate, validate_allocation

__all__ = [
    "Assign", "BinaryOp", "Goto", "IfGoto", "Instruction", "Label",
    "Operand", "ParseError", "Return", "parse", "BasicBlock",
    "ControlFlowGraph", "build_cfg",
    "LivenessResult", "analyze_liveness", "uses_defs", "InterferenceGraph",
    "build_interference",
    "Allocation", "allocate", "validate_allocation",
]
