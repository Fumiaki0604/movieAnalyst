from __future__ import annotations

from langgraph.graph import END, StateGraph

from agents import (
    advice_node,
    analysis_node,
    compile_report_node,
    extraction_node,
    interpretation_node,
)
from models import GraphState


def build_graph():
    """
    LangGraph ワークフローを構築して返す。

    パイプライン:
        extract_facts -> interpret -> analyze_issues -> generate_advice -> compile_report

    各ノードは GraphState を受け取り、部分的な状態更新を返す。
    Supervisor パターンへの拡張は、set_entry_point の前に
    supervisor ノードを追加し、条件付きエッジで各エージェントに振り分ける形で対応できる。
    """
    g = StateGraph(GraphState)

    g.add_node("extract_facts", extraction_node)
    g.add_node("interpret", interpretation_node)
    g.add_node("analyze_issues", analysis_node)
    g.add_node("generate_advice", advice_node)
    g.add_node("compile_report", compile_report_node)

    g.set_entry_point("extract_facts")
    g.add_edge("extract_facts", "interpret")
    g.add_edge("interpret", "analyze_issues")
    g.add_edge("analyze_issues", "generate_advice")
    g.add_edge("generate_advice", "compile_report")
    g.add_edge("compile_report", END)

    return g.compile()
