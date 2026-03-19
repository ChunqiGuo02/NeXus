"""NeXus 共享数据契约 — 所有 cross-skill JSON 文件的 schema 定义。

用 Pydantic v2 models 保证 stages/validators/skills 之间的数据一致性。
validators.py 在加载 JSON 时先通过此处的 model 验证。
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------- Evidence Graph ---------- #


class Claim(BaseModel):
    """evidence_graph.json 中的单条 claim。"""

    id: str
    type: str = Field(
        description="claim 类型",
        pattern="^(method|result|limitation|finding|comparison|background)$",
    )
    text: str = Field(min_length=5)
    source_paper_id: str
    exact_quote: str = ""
    confidence: float = Field(ge=0, le=1, default=0.8)
    publishable: bool = True  # False = shadow source, 禁止出现在终稿


class EvidenceGraph(BaseModel):
    """evidence_graph.json 的顶层 schema。"""

    claims: list[Claim] = []
    last_updated: str | None = None


# ---------- Corpus Ledger ---------- #


class CorpusEntry(BaseModel):
    """corpus_ledger.json 中的单条论文记录。"""

    id: str
    title: str
    year: int | None = None
    cite_key: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    access_state: Literal["fetched", "failed", "pending"] = "pending"
    publishable: bool = True
    citation_count: int | None = None


class CorpusLedger(BaseModel):
    """corpus_ledger.json 的顶层 schema。"""

    entries: list[CorpusEntry] = []


# ---------- Hypothesis Board ---------- #


class NoveltyRisk(BaseModel):
    """novelty-checker 的风险评估输出。"""

    overall_risk: Literal["high", "medium", "low", "unknown"]
    nearest_prior_art: list[dict[str, Any]] = []
    total_papers_scanned: int = 0
    recommendation: str = ""
    suggested_pivots: list[str] = []
    search_queries_used: list[str] = []


class Hypothesis(BaseModel):
    """hypothesis_board.json 中的单个 idea。"""

    id: str
    title: str = ""
    tier: str = ""
    description: str = ""
    selected: bool = False
    novelty_risk: NoveltyRisk | None = None
    thought_path: str = ""
    contribution_type: str = ""
    expected_delta: str = ""


class HypothesisBoard(BaseModel):
    """hypothesis_board.json 的顶层 schema。"""

    hypotheses: list[Hypothesis] = []


# ---------- Decision Log ---------- #


class Decision(BaseModel):
    """用户在硬卡点的决策记录。"""

    stage: str
    decision: str
    rationale: str = ""
    alternatives_considered: list[str] = []
    timestamp: str = ""


# ---------- Rollback Record ---------- #


class RollbackRecord(BaseModel):
    """一次回退的记录。"""

    from_stage: str
    to_stage: str
    reason: str = ""
    timestamp: str = ""


# ---------- Project State ---------- #


class ProjectState(BaseModel):
    """project_state.json 的顶层 schema — pipeline 全局状态。"""

    project_name: str = "untitled"
    current_stage: str | None = "insight_interview"
    user_level: Literal["expert", "intermediate", "novice"] = "intermediate"
    user_insights: dict[str, Any] = {}
    target_venue: str | None = None
    autopilot: bool = False
    sdp_mode: Literal["full", "lite", "same_model"] = "full"
    checkpoints_passed: list[str] = []
    stages_completed: list[str] = []
    rollback_history: list[RollbackRecord] = []
    decision_log: list[Decision] = []
    review_cycle: int = 0
    reentry_history: list[dict[str, Any]] = []
    compute_target: str = "local"
    stage_start_time: str | None = None
    created_at: str = ""
    updated_at: str = ""


# ---------- Experiment Results ---------- #


class MetricResult(BaseModel):
    """实验结果表中的一行。"""

    name: str
    value: float | None = None
    std: float | None = None
    num_seeds: int = 1


class ExperimentResults(BaseModel):
    """artifacts/experiment_results.json 的 schema。"""

    main_table: list[MetricResult] = []
    ablation_table: list[dict[str, Any]] = []


# ---------- Story Skeleton ---------- #


class WeaknessPreemption(BaseModel):
    """论文弱点预防条目。"""

    attack: str
    defense: str
    embed_in_section: str = ""


class StorySkeleton(BaseModel):
    """artifacts/story_skeleton.json 的 schema。"""

    one_sentence_summary: str = ""
    positioning: str = ""
    narrative_arc: str = ""
    sections: list[dict[str, Any]] = []
    abstract_formula: dict[str, str] = {}
    weakness_preemption: list[WeaknessPreemption] = []
    significance_argument: str = ""
    figure1_spec: str = ""


# ---------- Review Report ---------- #


class ReviewReport(BaseModel):
    """artifacts/review_round*.json 的 schema。"""

    reviews: list[dict[str, Any]] = []
    consensus: list[str] = []
    disagreements: list[str] = []
    must_fix: list[str] = []
    nice_to_have: list[str] = []
    overall_decision: str = ""


class MetaReview(BaseModel):
    """artifacts/meta_review.json 的 schema。"""

    decision: Literal["accept", "minor_revision", "major_revision", "reject"]
    summary: str = ""
    key_strengths: list[str] = []
    key_weaknesses: list[str] = []
    recommendation: str = ""


# ---------- Venue Playbook ---------- #


class VenuePlaybook(BaseModel):
    """venue_playbooks/playbooks.json 中的单个 venue 配置。"""

    venue: str
    acceptance_rate: str = ""
    max_pages: int | None = None
    required_sections: list[str] = []
    preferred_types: list[str] = []
    mandatory_experiments: list[str] = []
    common_reject_reasons: list[str] = []
    anonymization_patterns: list[str] = []
    exemplar_papers: list[str] = []


# ---------- Schema 验证辅助函数 ---------- #


def validate_json_schema(data: Any, model_cls: type[BaseModel]) -> list[str]:
    """尝试用 Pydantic model 验证数据，返回错误列表。空列表 = 通过。"""
    try:
        model_cls.model_validate(data)
        return []
    except Exception as e:
        return [f"Schema 验证失败 ({model_cls.__name__}): {e}"]
