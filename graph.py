from __future__ import annotations

from langgraph.graph import END, StateGraph

from agents import (
    advice_node,
    analysis_node,
    compile_report_node,
    extraction_node,
    interpretation_node,
    summary_node,
)
from models import GraphState


def build_graph(mode: str = "full"):
    """
    LangGraph ワークフローを構築して返す。

    mode="full"    : extract_facts -> interpret -> analyze_issues -> generate_advice -> compile_report
    mode="summary" : summary_node -> compile_report
    mode="none"    : compile_report のみ（字幕保存のみ）
    """
    g = StateGraph(GraphState)
    g.add_node("compile_report", compile_report_node)

    if mode == "full":
        g.add_node("extract_facts", extraction_node)
        g.add_node("interpret", interpretation_node)
        g.add_node("analyze_issues", analysis_node)
        g.add_node("generate_advice", advice_node)
        g.set_entry_point("extract_facts")
        g.add_edge("extract_facts", "interpret")
        g.add_edge("interpret", "analyze_issues")
        g.add_edge("analyze_issues", "generate_advice")
        g.add_edge("generate_advice", "compile_report")
    elif mode == "summary":
        g.add_node("summarize", summary_node)
        g.set_entry_point("summarize")
        g.add_edge("summarize", "compile_report")
    else:  # none
        g.set_entry_point("compile_report")

    g.add_edge("compile_report", END)
    return g.compile()
