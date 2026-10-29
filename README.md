# Intelligent Register Allocation Using Machine Learning for Code Generation

An educational Python project that parses a small three-address-code (TAC) language, analyzes control flow and liveness, constructs an interference graph, and compares graph-coloring allocations with traditional and ML spill ranking.

**The displayed allocation and pseudo-target report are not executable machine code.** This project has no target architecture, instruction selection, register constraints, calling convention, or code emitter.

## Installation

Python 3.10 or newer is required.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[ui,dev]"
```

For compiler analysis without the UI, install only the test extra with `python -m pip install -e ".[dev]"`. The ML spill ranker uses scikit-learn, included in the `ui` extra (or install with `.[ml]`).

## Run

```powershell
streamlit run app/streamlit_app.py
pytest -q
```

The interface loads `examples/branching.tac` by default. Edit the TAC, choose the number of registers, select a spill ranking strategy, and choose **Analyze and allocate**.

## Architecture

- `src/regalloc/ir.py`: immutable typed TAC instructions and operands.
- `src/regalloc/parser.py`: syntax validation and branch-label validation.
- `src/regalloc/cfg.py`: basic-block partitioning, CFG successors and predecessors.
- `src/regalloc/liveness.py`: use/definition extraction and iterative block plus instruction liveness.
- `src/regalloc/interference.py`: undirected graph built from definitions and live-out sets.
- `src/regalloc/allocator.py`: simplify/select coloring, unique abstract spill slots, and allocation validation.
- `src/regalloc/ml/`: program-derived spill features and a deterministic scikit-learn spill-cost ranker.
- `app/streamlit_app.py`: interface only; it calls the compiler package.
- `tests/`: focused unit and end-to-end tests.

## Supported TAC subset

One instruction per line. Identifiers use ASCII letter/underscore followed by letters, digits, or underscores. Operands are identifiers or signed decimal integer literals. Blank lines and text after `#` are ignored.

```text
x = y
x = y + 2
x = y - z
x = y * z
x = y / z
x = y % z
goto label
if x goto label
if x < y goto label
if x == 0 goto label
label:
label: x = 1
return
return x
```

Arithmetic operators are `+ - * / %`; conditional operators are `== != < <= > >=`. Every branch target must name a declared label. Labels are unique. Unsupported features include function calls, parameters, arrays, memory addressing, unary operators, strings, and typed declarations. Variables are treated as untyped names; the parser does not enforce declaration-before-use.

## Design and limitations

Liveness reaches a fixed point over CFG blocks using `IN = USE union (OUT minus DEF)` and `OUT = union(IN(successors))`. Interference is added between each instruction's definitions and values live afterward, with the standard copy-source omission for simple assignments. Simultaneously live values also interfere, including live-in values that are used but not defined within the input fragment.

The allocator uses simplify/select graph coloring. When all remaining nodes have degree at least `K`, it selects a potential spill using the supplied spill cost; after selection, any node that cannot be colored receives its own abstract spill slot. It does not rewrite TAC with load/store operations. The traditional comparator uses a degree-only spill-cost heuristic.

The ML ranker extracts use count, live extent, next-use distance, and interference degree. Its demonstration model is trained on deterministic synthetic labels from `3 * use_count + live_range + 0.25 * next_use_distance - 2 * interference_degree`. Lower predicted cost is selected first for spilling. The traditional baseline uses `1 / (interference_degree + 1)`, also selecting lower cost first. The model illustrates how features affect ranking; it is not trained on execution measurements and does not establish that ML improves generated code. Allocation validity is always checked from the interference graph, independent of ranking strategy.

The UI reports blocks, live sets, graph neighbors, register assignments, spill slots, and a **pseudo-target allocation report**. No native or executable target code is generated.

## Tests

```powershell
pytest -q
```

Tests cover TAC instruction variants, comments and labels, malformed/unsupported syntax, undefined targets, CFG edges, loop liveness, interference, graph coloring, forced spills, ML features/ranking, and validation of interfering assignments.

## Example result

For `examples/branching.tac` with three registers, analysis identifies a loop backedge from the conditional branch to `loop`, computes the live values at block boundaries, and colors the interference graph. Exact register names may depend on graph ordering. With fewer registers than a live clique needs, the allocator reports variables in distinct abstract spill slots; the report is not executable code.
