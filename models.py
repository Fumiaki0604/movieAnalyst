from __future__ import annotations

from typing import Optional, TypedDict

from pydantic import BaseModel, Field


# --- Structured output models (LLM response schemas) ---

class Fact(BaseModel):
    label: str = Field(description="事実の短いラベル（例: '機械学習の基礎説明が含まれる'）")
    description: str = Field(description="事実の詳細説明")
    evidence_ids: list[str] = Field(
        default_factory=list,
        description="根拠のevent_idリスト（例: ['t0012', 't0023']）",
    )
    timestamp_start: Optional[float] = Field(
        None, description="最初の根拠の開始時刻（秒）"
    )


class Interpretation(BaseModel):
    label: str = Field(description="解釈の短いラベル")
    explanation: str = Field(description="視聴者プロフィールを踏まえた解釈の詳細")
    evidence_ids: list[str] = Field(default_factory=list)
    relevance: str = Field(description="この内容が視聴者にとってなぜ重要/不要か")


class Issue(BaseModel):
    label: str = Field(description="問題点・課題のラベル")
    severity: str = Field(description="重要度: 'high' | 'medium' | 'low'")
    description: str = Field(description="問題点の詳細説明")
    evidence_ids: list[str] = Field(default_factory=list)


class AdviceItem(BaseModel):
    title: str = Field(description="アドバイスのタイトル")
    action: str = Field(description="具体的なアクション（何をするか）")
    context: str = Field(description="どの場面・状況で意識すべきか")
    measure: str = Field(description="効果の確認方法・測定方法")
    evidence_ids: list[str] = Field(default_factory=list)
    priority: str = Field(description="優先度: 'high' | 'medium' | 'low'")


# --- Wrappers for structured output parsing ---

class ExtractionOutput(BaseModel):
    facts: list[Fact] = Field(description="抽出した事実のリスト（5〜10件）")


class InterpretationOutput(BaseModel):
    interpretations: list[Interpretation] = Field(
        description="視聴者視点の解釈リスト（3〜7件）"
    )


class IssueOutput(BaseModel):
    issues: list[Issue] = Field(description="特定した問題点・課題リスト（2〜5件）")


class AdviceOutput(BaseModel):
    advice: list[AdviceItem] = Field(description="改善アドバイスリスト（3〜5件）")
    summary: str = Field(description="動画全体の一言まとめ（1〜2文）")


# --- LangGraph state ---

class GraphState(TypedDict):
    video_id: str
    video_url: str
    profile: dict
    evidence_timeline: list[dict]  # list of EvidenceItem dicts
    facts: list[dict]
    interpretations: list[dict]
    issues: list[dict]
    advice: list[dict]
    summary: str
    final_report: dict
