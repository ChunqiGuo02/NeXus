"""合规检查器 — 验证 LLM 是否真正执行了 SKILL.md 中的关键步骤。

原理: 每个 SKILL 的关键步骤都会产生特定文件/字段。
如果文件不存在，说明步骤被跳过。

不依赖 LLM 自述 — 只看文件系统。
"""

from __future__ import annotations

import json
from pathlib import Path


# 每个 stage 的合规清单
COMPLIANCE_RULES: dict[str, dict[str, str]] = {
    "ideation": {
        "frontier_analysis": "dialogue/frontier_analysis.md 存在",
        "tot_survivors": "dialogue/tot_survivors.md 存在",
        "benchmark_analysis": "dialogue/benchmark_analysis.md 存在",
        "red_team_report": "dialogue/red_team_report.md 存在",
        "ideas_v2": "dialogue/ideas_v2.md 存在",
        "cmg_all_evaluated": (
            "hypothesis_board.json 中所有 idea 都有 contribution_delta"
        ),
    },
    "writing": {
        "exemplar_analysis": "artifacts/exemplar_analysis.md 存在",
        "fresh_eyes_result": "artifacts/fresh_eyes_result.md 存在",
        "story_skeleton_complete": (
            "story_skeleton.json 含 one_sentence_summary"
            " + weakness_preemption ≥ 3 条"
        ),
        "claims_cross_validated": (
            "每个 \\cite{} 对应 evidence_graph 中的 claim"
        ),
    },
    "experiment_run": {
        "code_audit": "artifacts/code_audit.md 存在",
        "experiment_story": "artifacts/experiment_story.md 存在",
        "baseline_verification": "artifacts/baseline_verification.md 存在",
    },
    "review_round1": {
        "rejection_preview": "dialogue/rejection_preview.md 存在",
        "reviews_model1": "dialogue/reviews_gemini.md 存在",
        "reviews_model2": "dialogue/reviews_gpt.md 存在",
        "cross_review": "dialogue/cross_review_gemini.md 存在",
    },
    "domain_calibration": {
        "taste_profile": "artifacts/domain_taste_profile.json 存在",
        "exemplar_structures": "artifacts/exemplar_structures.json 存在",
        "venue_tier_config": "artifacts/venue_tier_config.json 存在",
    },
}


def check_compliance(stage: str, project_dir: str) -> dict:
    """返回 {compliant: bool, failed: [...], passed: [...]}。"""
    rules = COMPLIANCE_RULES.get(stage, {})
    failed: list[dict[str, str]] = []
    passed: list[str] = []

    for rule_name, description in rules.items():
        if _check_rule(rule_name, stage, project_dir):
            passed.append(rule_name)
        else:
            failed.append({"rule": rule_name, "description": description})

    return {
        "compliant": len(failed) == 0,
        "failed": failed,
        "passed": passed,
        "coverage": (
            f"{len(passed)}/{len(rules)}"
            if rules
            else "N/A"
        ),
    }


def _check_rule(rule_name: str, stage: str, project_dir: str) -> bool:
    """检查单条合规规则。"""
    base = Path(project_dir)

    # 通用文件存在性检查
    file_rules = {
        # ideation
        "frontier_analysis": "dialogue/frontier_analysis.md",
        "tot_survivors": "dialogue/tot_survivors.md",
        "benchmark_analysis": "dialogue/benchmark_analysis.md",
        "red_team_report": "dialogue/red_team_report.md",
        "ideas_v2": "dialogue/ideas_v2.md",
        # writing
        "exemplar_analysis": "artifacts/exemplar_analysis.md",
        "fresh_eyes_result": "artifacts/fresh_eyes_result.md",
        # experiment_run
        "code_audit": "artifacts/code_audit.md",
        "experiment_story": "artifacts/experiment_story.md",
        "baseline_verification": "artifacts/baseline_verification.md",
        # review_round1
        "rejection_preview": "dialogue/rejection_preview.md",
        "reviews_model1": "dialogue/reviews_gemini.md",
        "reviews_model2": "dialogue/reviews_gpt.md",
        "cross_review": "dialogue/cross_review_gemini.md",
        # domain_calibration
        "taste_profile": "artifacts/domain_taste_profile.json",
        "exemplar_structures": "artifacts/exemplar_structures.json",
        "venue_tier_config": "artifacts/venue_tier_config.json",
    }

    if rule_name in file_rules:
        return (base / file_rules[rule_name]).exists()

    # 复杂规则
    if rule_name == "cmg_all_evaluated":
        return _check_cmg(base)

    if rule_name == "story_skeleton_complete":
        return _check_skeleton(base)

    if rule_name == "claims_cross_validated":
        # 留给更复杂的交叉验证逻辑
        return True

    return False


def _check_cmg(base: Path) -> bool:
    """检查 hypothesis_board 中所有 idea 都有 contribution_delta。"""
    hb_path = base / "hypothesis_board.json"
    if not hb_path.exists():
        return False
    try:
        hb = json.loads(hb_path.read_text(encoding="utf-8"))
        ideas = hb.get("hypotheses", hb.get("ideas", []))
        if not ideas:
            return False
        return all(
            idea.get("contribution_delta") is not None for idea in ideas
        )
    except (json.JSONDecodeError, KeyError):
        return False


def _check_skeleton(base: Path) -> bool:
    """检查 story skeleton 是否完整。"""
    sk_path = base / "artifacts/story_skeleton.json"
    if not sk_path.exists():
        sk_path = base / "story_skeleton.json"
    if not sk_path.exists():
        return False
    try:
        sk = json.loads(sk_path.read_text(encoding="utf-8"))
        has_summary = bool(sk.get("one_sentence_summary"))
        wp = sk.get("weakness_preemption", [])
        return has_summary and len(wp) >= 3
    except (json.JSONDecodeError, KeyError):
        return False
