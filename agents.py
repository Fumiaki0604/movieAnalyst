from __future__ import annotations

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from config import profile_to_text
from models import (
    AdviceOutput,
    ExtractionOutput,
    GraphState,
    InterpretationOutput,
    IssueOutput,
)

MODEL = "claude-sonnet-4-6"


def _llm():
    return ChatAnthropic(model=MODEL, temperature=0)


def _fmt_timeline(timeline: list[dict], max_chars: int = 14000) -> str:
    lines = []
    total = 0
    for item in timeline:
        s = item["start"]
        m, sec = int(s // 60), int(s % 60)
        line = f"[{m:02d}:{sec:02d}] ({item['event_id']}) {item['text']}"
        total += len(line) + 1
        if total > max_chars:
            lines.append("... (以降省略)")
            break
        lines.append(line)
    return "\n".join(lines)


def _fmt_facts(facts: list[dict]) -> str:
    lines = []
    for f in facts:
        ids = ", ".join(f.get("evidence_ids", []))
        lines.append(f"- [{ids}] {f['label']}: {f['description']}")
    return "\n".join(lines)


def _fmt_interpretations(interps: list[dict]) -> str:
    lines = []
    for i in interps:
        ids = ", ".join(i.get("evidence_ids", []))
        lines.append(f"- [{ids}] {i['label']}: {i['explanation']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Agent Nodes
# ---------------------------------------------------------------------------

def extraction_node(state: GraphState) -> dict:
    """Agent 1 — 事実抽出: タイムラインから観測事実を抽出する。"""
    print("  [1/4] 事実抽出中...")

    llm = _llm().with_structured_output(ExtractionOutput)
    timeline_text = _fmt_timeline(state["evidence_timeline"])
    profile_ctx = profile_to_text(state["profile"])

    result = llm.invoke(
        [
            SystemMessage(
                content=(
                    "あなたは動画コンテンツの事実抽出エージェントです。"
                    "タイムスタンプ付きのトランスクリプトから、重要な事実・主張・情報を抽出してください。"
                    "各事実には根拠となる event_id を必ず含めてください。"
                )
            ),
            HumanMessage(
                content=(
                    f"【視聴者プロフィール】\n{profile_ctx}\n\n"
                    f"【エビデンスタイムライン】\n{timeline_text}\n\n"
                    "上記の動画から重要な事実を5〜10件抽出してください。"
                )
            ),
        ]
    )
    return {"facts": [f.model_dump() for f in result.facts]}


def interpretation_node(state: GraphState) -> dict:
    """Agent 2 — 解釈: 事実を視聴者プロフィールに照らして解釈する。"""
    print("  [2/4] 解釈中...")

    llm = _llm().with_structured_output(InterpretationOutput)
    facts_text = _fmt_facts(state["facts"])
    profile_ctx = profile_to_text(state["profile"])
    timeline_sample = _fmt_timeline(state["evidence_timeline"], max_chars=4000)

    result = llm.invoke(
        [
            SystemMessage(
                content=(
                    "あなたは動画コンテンツの解釈エージェントです。"
                    "抽出された事実と視聴者のプロフィールを照らし合わせ、"
                    "この動画内容が視聴者にとって何を意味するかを解釈してください。"
                )
            ),
            HumanMessage(
                content=(
                    f"【視聴者プロフィール】\n{profile_ctx}\n\n"
                    f"【抽出された事実】\n{facts_text}\n\n"
                    f"【タイムライン（参考）】\n{timeline_sample}\n\n"
                    "視聴者の目標・スキルレベル・現在の関心を踏まえ、3〜7件の解釈を生成してください。"
                )
            ),
        ]
    )
    return {"interpretations": [i.model_dump() for i in result.interpretations]}


def analysis_node(state: GraphState) -> dict:
    """Agent 3 — 問題点分析: 視聴者が直面する課題・ギャップを特定する。"""
    print("  [3/4] 問題点分析中...")

    llm = _llm().with_structured_output(IssueOutput)
    facts_text = _fmt_facts(state["facts"])
    interp_text = _fmt_interpretations(state["interpretations"])
    profile_ctx = profile_to_text(state["profile"])

    result = llm.invoke(
        [
            SystemMessage(
                content=(
                    "あなたは問題点分析エージェントです。"
                    "動画の内容と視聴者への解釈をもとに、"
                    "視聴者が直面している課題・ギャップ・注意すべき点を特定してください。"
                )
            ),
            HumanMessage(
                content=(
                    f"【視聴者プロフィール】\n{profile_ctx}\n\n"
                    f"【事実】\n{facts_text}\n\n"
                    f"【解釈】\n{interp_text}\n\n"
                    "視聴者にとって重要な問題点・課題を2〜5件特定してください。"
                )
            ),
        ]
    )
    return {"issues": [i.model_dump() for i in result.issues]}


def advice_node(state: GraphState) -> dict:
    """Agent 4 — アドバイス生成: 具体的・測定可能なアドバイスを生成する。"""
    print("  [4/4] アドバイス生成中...")

    llm = _llm().with_structured_output(AdviceOutput)
    facts_text = _fmt_facts(state["facts"])
    issues_text = "\n".join(
        f"- [{i.get('severity', '?')}] {i['label']}: {i['description']}"
        for i in state["issues"]
    )
    profile_ctx = profile_to_text(state["profile"])

    result = llm.invoke(
        [
            SystemMessage(
                content=(
                    "あなたは実践的アドバイス生成エージェントです。"
                    "特定された問題点をもとに、視聴者が今すぐ実行できる具体的なアドバイスを生成してください。"
                    "アドバイスは抽象的な心構えではなく、具体的なアクションと測定方法まで落とし込んでください。"
                )
            ),
            HumanMessage(
                content=(
                    f"【視聴者プロフィール】\n{profile_ctx}\n\n"
                    f"【事実（参考）】\n{facts_text}\n\n"
                    f"【特定された問題点】\n{issues_text}\n\n"
                    "3〜5件の具体的アドバイスと動画全体の一言まとめを生成してください。"
                )
            ),
        ]
    )
    return {
        "advice": [a.model_dump() for a in result.advice],
        "summary": result.summary,
    }


def compile_report_node(state: GraphState) -> dict:
    """最終レポートを組み立てる（LLM 呼び出しなし）。"""
    report = {
        "video_id": state["video_id"],
        "video_url": state["video_url"],
        "summary": state["summary"],
        "facts": state["facts"],
        "interpretations": state["interpretations"],
        "issues": state["issues"],
        "advice": state["advice"],
        "evidence_timeline": state["evidence_timeline"],  # フロントエンドのタイムスタンプ解決に使用
    }
    return {"final_report": report}
