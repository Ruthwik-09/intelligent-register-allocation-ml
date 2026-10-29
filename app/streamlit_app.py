"""Streamlit interface for the educational TAC register allocator."""

from pathlib import Path
import sys

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from regalloc import (  # noqa: E402
    analyze_liveness, allocate, build_cfg, build_interference,
    parse, validate_allocation,
)
from regalloc.ml import extract_features, train_ranker  # noqa: E402


st.set_page_config(page_title="Intelligent Register Allocation", layout="wide")
st.title("Intelligent Register Allocation")
st.caption("Educational TAC analysis and register allocation. Displayed results are reports and pseudo-target examples, not executable machine code.")

example_path = ROOT / "examples" / "branching.tac"
default_source = example_path.read_text(encoding="utf-8")
source = st.text_area("Three-address code", value=default_source, height=260)
col1, col2 = st.columns(2)
with col1:
    register_count = st.number_input("Available registers", min_value=1, max_value=16,
                                     value=3, step=1)
with col2:
    method = st.selectbox("Spill ranking", ["Traditional heuristic", "ML spill ranker", "Compare both"])

if st.button("Analyze and allocate", type="primary"):
    try:
        instructions = parse(source)
        cfg = build_cfg(instructions)
        liveness = analyze_liveness(cfg)
        graph = build_interference(cfg, liveness)
        features = extract_features(instructions, graph, liveness)
    except (ValueError, TypeError) as exc:
        st.error(str(exc))
    else:
        st.subheader("Basic blocks and control flow")
        st.json({str(block.id): {
            "label": block.label,
            "instructions": [type(instruction).__name__ for instruction in block.instructions],
            "successors": sorted(cfg.successors[block.id]),
            "live_in": sorted(liveness.live_in[block.id]),
            "live_out": sorted(liveness.live_out[block.id]),
        } for block in cfg.blocks})
        st.subheader("Interference graph")
        st.json({name: sorted(neighbors) for name, neighbors in graph.neighbors.items()})

        options = ["Traditional heuristic", "ML spill ranker"] if method == "Compare both" else [method]
        ml_ranker = train_ranker(features) if "ML spill ranker" in options else None
        for choice in options:
            score = (None if choice == "Traditional heuristic"
                     else lambda name, current_graph: ml_ranker(name, current_graph))
            allocation = allocate(graph, [f"R{i+1}" for i in range(register_count)], score)
            violations = validate_allocation(graph, allocation)
            st.subheader(choice)
            st.write({"registers": allocation.registers,
                      "spill_slots": {name: f"spill[{slot}]" for name, slot in allocation.spills.items()},
                      "valid": not violations})
            if violations:
                st.error("; ".join(violations))
            st.markdown("**Illustrative pseudo-target allocation report**")
            st.code("\n".join(
                f"{name} -> {allocation.registers[name]}" if name in allocation.registers
                else f"{name} -> spill[{allocation.spills[name]}]"
                for name in sorted(graph.variables)
            ) or "No variables")
        st.caption("The ML model is trained on deterministic synthetic spill-cost labels. Results demonstrate feature-based ranking, not measured execution-time improvement.")
