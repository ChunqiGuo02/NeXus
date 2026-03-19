"""Comprehensive tests for Pipeline Orchestrator v2.

Covers:
- 18 stage definitions + chain integrity
- Rollback logic (3 scenarios)
- 3-round review sub-stages
- reenter_pipeline tool
- All 18 validators (pass/fail)
- User level + venue tracking
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from stages import STAGES, STAGE_ORDER, get_stage, get_next_stage, get_rollback_stage, build_subagent_tasks
from validators import validate_stage


# ============================================================
# 辅助
# ============================================================


def _write_json(tmp: Path, rel: str, data: dict | list) -> None:
    p = tmp / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _write_text(tmp: Path, rel: str, text: str = "ok") -> None:
    p = tmp / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


# ============================================================
# Stage Definitions
# ============================================================


class TestStageDefinitions:
    """Stage 定义完整性测试。"""

    def test_total_stages(self):
        assert len(STAGES) == 18, f"Expected 18 stages, got {len(STAGES)}"

    def test_stage_order_matches_registry(self):
        for name in STAGE_ORDER:
            assert name in STAGES, f"{name} in STAGE_ORDER but not in STAGES"

    def test_chain_integrity(self):
        """每个 stage 的 next_stage 指向有效的 stage 或 None。"""
        for name, stage in STAGES.items():
            if stage.next_stage is not None:
                assert stage.next_stage in STAGES, (
                    f"{name}.next_stage='{stage.next_stage}' not in STAGES"
                )

    def test_rollback_targets_valid(self):
        """回退目标必须指向有效 stage。"""
        for name, stage in STAGES.items():
            if stage.rollback_stage is not None:
                assert stage.rollback_stage in STAGES, (
                    f"{name}.rollback_stage='{stage.rollback_stage}' not in STAGES"
                )

    def test_hard_checkpoints(self):
        checkpoints = [n for n, s in STAGES.items() if s.is_hard_checkpoint]
        expected = {
            "survey_search", "ideation", "novelty_check",
            "experiment_design", "pilot_experiment",
            "venue_fit_check", "review_round3_meta",
        }
        assert set(checkpoints) == expected

    def test_parallel_stages(self):
        parallel = [n for n, s in STAGES.items() if s.parallel]
        expected = {"survey_fetch", "deep_dive", "experiment_run", "review_round1"}
        assert set(parallel) == expected

    def test_sdp_stages(self):
        sdp = [n for n, s in STAGES.items() if s.requires_model_switch]
        expected = {
            "ideation", "experiment_design", "writing",
            "review_round1", "review_round2", "review_round3_meta",
        }
        assert set(sdp) == expected

    def test_rollback_stages(self):
        rollback = [n for n, s in STAGES.items() if s.rollback_stage]
        expected = {
            "novelty_check", "pilot_experiment",
            "experiment_run", "review_round3_meta",
        }
        assert set(rollback) == expected

    def test_review_sub_stages(self):
        subs = [n for n, s in STAGES.items() if s.is_sub_stage]
        assert len(subs) == 5  # round1, revise1, round2, revise2, round3_meta
        for name in subs:
            assert STAGES[name].parent_stage == "review"

    def test_pipeline_starts_with_insight_interview(self):
        assert STAGE_ORDER[0] == "insight_interview"

    def test_pipeline_ends_with_final_revise(self):
        assert STAGE_ORDER[-1] == "final_revise"
        assert STAGES["final_revise"].next_stage is None

    def test_new_stages_exist(self):
        for name in ["insight_interview", "pilot_experiment", "venue_fit_check"]:
            assert name in STAGES


# ============================================================
# Rollback
# ============================================================


class TestRollback:

    def test_get_rollback_stage(self):
        rb = get_rollback_stage("pilot_experiment")
        assert rb is not None
        assert rb.name == "ideation"

    def test_get_rollback_stage_none(self):
        rb = get_rollback_stage("survey_search")
        assert rb is None

    def test_novelty_check_rollback_target(self):
        rb = get_rollback_stage("novelty_check")
        assert rb.name == "ideation"

    def test_experiment_run_rollback_target(self):
        rb = get_rollback_stage("experiment_run")
        assert rb.name == "experiment_design"

    def test_review_round3_rollback_target(self):
        rb = get_rollback_stage("review_round3_meta")
        assert rb.name == "experiment_run"


# ============================================================
# Subagent Tasks
# ============================================================


class TestSubagentTasks:

    def test_parallel_stage_generates_tasks(self):
        stage = get_stage("review_round1")
        items = [{"id": f"r{i}", "title": f"Reviewer {i}"} for i in range(6)]
        tasks = build_subagent_tasks(stage, items)
        assert len(tasks) == 6

    def test_non_parallel_returns_empty(self):
        stage = get_stage("ideation")
        tasks = build_subagent_tasks(stage, [{"id": "1"}])
        assert tasks == []

    def test_max_parallel_respected(self):
        stage = get_stage("deep_dive")
        items = [{"id": str(i)} for i in range(10)]
        tasks = build_subagent_tasks(stage, items)
        assert len(tasks) == stage.max_parallel


# ============================================================
# Validators
# ============================================================


class TestValidators:

    def test_insight_interview_missing(self, tmp_path):
        errors = validate_stage("insight_interview", str(tmp_path))
        assert any("project_state.json" in e for e in errors)

    def test_insight_interview_no_level(self, tmp_path):
        _write_json(tmp_path, "project_state.json", {"user_level": "", "target_venue": ""})
        errors = validate_stage("insight_interview", str(tmp_path))
        assert len(errors) >= 1

    def test_insight_interview_pass(self, tmp_path):
        _write_json(tmp_path, "project_state.json", {
            "user_level": "novice", "target_venue": "NeurIPS"
        })
        errors = validate_stage("insight_interview", str(tmp_path))
        assert errors == []

    def test_survey_search_pass(self, tmp_path):
        _write_json(tmp_path, "corpus_ledger.json", {"entries": [{"id": "1", "title": "Paper"}]})
        assert validate_stage("survey_search", str(tmp_path)) == []

    def test_survey_search_empty(self, tmp_path):
        _write_json(tmp_path, "corpus_ledger.json", {"entries": []})
        errors = validate_stage("survey_search", str(tmp_path))
        assert len(errors) == 1

    def test_survey_fetch_pass(self, tmp_path):
        _write_json(tmp_path, "evidence_graph.json", {
            "claims": [{"id": str(i), "type": "method", "text": f"Claim {i}",
                        "source_paper_id": f"p{i}"} for i in range(10)]
        })
        _write_text(tmp_path, "artifacts/survey.md")
        assert validate_stage("survey_fetch", str(tmp_path)) == []

    def test_survey_fetch_few_claims(self, tmp_path):
        _write_json(tmp_path, "evidence_graph.json", {
            "claims": [{"id": "1", "type": "result", "text": "Test claim",
                        "source_paper_id": "p1"}]
        })
        _write_text(tmp_path, "artifacts/survey.md")
        errors = validate_stage("survey_fetch", str(tmp_path))
        assert any("不足 10 条" in e for e in errors)

    def test_evidence_audit_pass(self, tmp_path):
        _write_text(tmp_path, "evidence_audit.md")
        assert validate_stage("evidence_audit", str(tmp_path)) == []

    def test_ideation_pass(self, tmp_path):
        _write_json(tmp_path, "hypothesis_board.json", {
            "hypotheses": [{"id": "h1", "selected": True, "contribution_delta": {
                "delta_method": {"score": 4}, "delta_performance": {"score": 3},
                "delta_scope": {"score": 3}, "delta_insight": {"score": 4}}}]
        })
        assert validate_stage("ideation", str(tmp_path)) == []

    def test_ideation_no_selection(self, tmp_path):
        _write_json(tmp_path, "hypothesis_board.json", {
            "hypotheses": [{"id": "h1", "selected": False}]
        })
        errors = validate_stage("ideation", str(tmp_path))
        assert len(errors) == 1

    def test_deep_dive_pass(self, tmp_path):
        _write_text(tmp_path, "artifacts/deep_dive_paper1.md")
        assert validate_stage("deep_dive", str(tmp_path)) == []

    def test_novelty_check_pass(self, tmp_path):
        _write_json(tmp_path, "hypothesis_board.json", {
            "hypotheses": [{"id": "h1", "selected": True, "novelty_risk": {"level": "low"},
                            "contribution_delta": {
                                "delta_method": {"score": 3}, "delta_performance": {"score": 4},
                                "delta_scope": {"score": 3}, "delta_insight": {"score": 3}}}]
        })
        assert validate_stage("novelty_check", str(tmp_path)) == []

    def test_novelty_check_missing_risk(self, tmp_path):
        _write_json(tmp_path, "hypothesis_board.json", {
            "hypotheses": [{"id": "h1", "selected": True}]  # no novelty_risk
        })
        errors = validate_stage("novelty_check", str(tmp_path))
        assert len(errors) == 1

    def test_experiment_design_pass(self, tmp_path):
        _write_text(tmp_path, "experimental_design.md")
        assert validate_stage("experiment_design", str(tmp_path)) == []

    def test_pilot_experiment_pass(self, tmp_path):
        _write_json(tmp_path, "artifacts/pilot_results.json", {"status": "pass"})
        assert validate_stage("pilot_experiment", str(tmp_path)) == []

    def test_pilot_experiment_missing(self, tmp_path):
        errors = validate_stage("pilot_experiment", str(tmp_path))
        assert len(errors) == 1

    def test_experiment_run_pass(self, tmp_path):
        _write_text(tmp_path, "artifacts/experiment_report.md")
        _write_json(tmp_path, "artifacts/experiment_results.json", {
            "main_table": [{"name": "acc", "value": 0.95, "std": 0.01, "num_seeds": 3}],
        })
        assert validate_stage("experiment_run", str(tmp_path)) == []

    def test_experiment_run_low_seeds(self, tmp_path):
        _write_text(tmp_path, "artifacts/experiment_report.md")
        _write_json(tmp_path, "artifacts/experiment_results.json", {
            "main_table": [{"name": "acc", "value": 0.95, "num_seeds": 1}],
        })
        errors = validate_stage("experiment_run", str(tmp_path))
        assert any("seed" in e for e in errors)

    def test_experiment_run_no_std(self, tmp_path):
        _write_text(tmp_path, "artifacts/experiment_report.md")
        _write_json(tmp_path, "artifacts/experiment_results.json", {
            "main_table": [{"name": "acc", "value": 0.95, "num_seeds": 3}],
        })
        errors = validate_stage("experiment_run", str(tmp_path))
        assert any("std" in e for e in errors)

    def test_venue_fit_check_pass(self, tmp_path):
        _write_text(tmp_path, "artifacts/venue_fit_report.md")
        assert validate_stage("venue_fit_check", str(tmp_path)) == []

    def test_writing_pass(self, tmp_path):
        # quality_engine v5 需要更完整的 tex 内容
        tex = (
            "\\section{Introduction}\n\n"
            "To address the challenge of X, we propose Y. "
            "This improves by 5% over baseline because it captures Z.\n\n"
            "Unlike prior work, our approach results in better generalization.\n\n"
            "\\section{Method}\n\n"
            "To overcome limitation A, we define:\n"
            "\\begin{equation} L = L_1 + L_2 \\end{equation}\n\n"
            "This allows us to model hierarchical structure. "
            "Compared to B, this reduces by 10% the error.\n\n"
            "\\section{Experiments}\n\n"
            "\\subsection{Setup}\n"
            "Implementation details of our method.\n\n"
            "\\subsection{Main Results}\n"
            "\\begin{figure}\\caption{Method overview}\\end{figure}\n"
            "Our method achieves 92.3% accuracy.\n\n"
            "\\subsection{Ablation}\n"
            "ablation study component analysis\n\n"
            "\\subsection{Analysis}\n"
            "case study error analysis qualitative visualization\n\n"
            "\\subsection{Limitation}\n"
            "failure limitation when it fails\n\n"
            "sensitivity robustness efficiency speed\n\n"
        )
        _write_text(tmp_path, "artifacts/draft_final.tex", tex)
        _write_json(tmp_path, "artifacts/story_skeleton.json", {
            "one_sentence_summary": "We show X.",
            "weakness_preemption": [{"attack": "a", "defense": "d"}],
            "contributions": ["method overview"],
        })
        assert validate_stage("writing", str(tmp_path)) == []

    def test_writing_shadow_source(self, tmp_path):
        _write_text(tmp_path, "artifacts/draft_final.tex", "\\cite{shadow_paper}")
        _write_json(tmp_path, "artifacts/story_skeleton.json", {})
        _write_json(tmp_path, "evidence_graph.json", {"claims": []})
        _write_json(tmp_path, "corpus_ledger.json", {
            "entries": [{"cite_key": "shadow_paper", "publishable": False}]
        })
        errors = validate_stage("writing", str(tmp_path))
        assert any("shadow source" in e for e in errors)

    def test_review_round1_pass(self, tmp_path):
        _write_json(tmp_path, "artifacts/review_round1.json", {"reviews": []})
        assert validate_stage("review_round1", str(tmp_path)) == []

    def test_revise_round1_pass(self, tmp_path):
        _write_text(tmp_path, "artifacts/draft_final.tex")
        assert validate_stage("revise_round1", str(tmp_path)) == []

    def test_review_round2_pass(self, tmp_path):
        _write_json(tmp_path, "artifacts/review_round2.json", {"reviews": []})
        assert validate_stage("review_round2", str(tmp_path)) == []

    def test_revise_round2_pass(self, tmp_path):
        _write_text(tmp_path, "artifacts/draft_final.tex")
        assert validate_stage("revise_round2", str(tmp_path)) == []

    def test_review_round3_meta_pass(self, tmp_path):
        _write_json(tmp_path, "artifacts/meta_review.json", {"decision": "accept"})
        assert validate_stage("review_round3_meta", str(tmp_path)) == []

    def test_final_revise_pass(self, tmp_path):
        _write_text(tmp_path, "artifacts/draft_final.tex", "\\documentclass{article}")
        _write_text(tmp_path, "artifacts/reproducibility_checklist.md")
        assert validate_stage("final_revise", str(tmp_path)) == []

    def test_final_revise_missing_checklist(self, tmp_path):
        _write_text(tmp_path, "artifacts/draft_final.tex")
        errors = validate_stage("final_revise", str(tmp_path))
        assert any("reproducibility_checklist" in e for e in errors)

    def test_final_revise_citation_consistency(self, tmp_path):
        _write_text(tmp_path, "artifacts/draft_final.tex",
                    "\\cite{paper_a} \\cite{paper_b}")
        _write_text(tmp_path, "artifacts/reproducibility_checklist.md")
        _write_text(tmp_path, "references.bib",
                    "@article{paper_a, title={A}}\n")  # paper_b missing
        errors = validate_stage("final_revise", str(tmp_path))
        assert any("paper_b" in e for e in errors)

    def test_unknown_stage(self, tmp_path):
        errors = validate_stage("nonexistent", str(tmp_path))
        assert any("未知" in e for e in errors)


# ============================================================
# Server Tools (integration-style)
# ============================================================


class TestAdvancePipeline:

    def test_initial_state(self, tmp_path):
        from server import advance_pipeline
        result = advance_pipeline(str(tmp_path))
        assert result["status"] == "active"
        assert result["stage_name"] == "insight_interview"

    def test_returns_user_level(self, tmp_path):
        from server import advance_pipeline
        result = advance_pipeline(str(tmp_path))
        assert "user_level" in result

    def test_rollback_info_included(self, tmp_path):
        _write_json(tmp_path, "project_state.json", {
            "current_stage": "pilot_experiment",
            "stages_completed": [
                "insight_interview", "survey_search", "survey_fetch",
                "evidence_audit", "ideation", "deep_dive", "novelty_check",
                "experiment_design",
            ],
        })
        from server import advance_pipeline
        result = advance_pipeline(str(tmp_path))
        assert result["rollback"]["enabled"] is True
        assert result["rollback"]["target_stage"] == "ideation"

    def test_no_rollback_for_survey(self, tmp_path):
        _write_json(tmp_path, "project_state.json", {
            "current_stage": "survey_search",
            "stages_completed": ["insight_interview"],
        })
        from server import advance_pipeline
        result = advance_pipeline(str(tmp_path))
        assert result["rollback"]["enabled"] is False

    def test_completed_pipeline(self, tmp_path):
        _write_json(tmp_path, "project_state.json", {
            "current_stage": None,
            "stages_completed": list(STAGE_ORDER),
        })
        from server import advance_pipeline
        result = advance_pipeline(str(tmp_path))
        assert result["status"] == "completed"


class TestCompleteStage:

    def test_wrong_stage(self, tmp_path):
        from server import complete_stage
        result = complete_stage(str(tmp_path), "ideation")
        assert result["status"] == "error"

    def test_rollback(self, tmp_path):
        _write_json(tmp_path, "project_state.json", {
            "current_stage": "pilot_experiment",
        })
        _write_json(tmp_path, "artifacts/pilot_results.json", {"status": "fail"})
        from server import complete_stage
        result = complete_stage(str(tmp_path), "pilot_experiment", result="rollback")
        assert result["status"] == "rolled_back"
        assert result["to_stage"] == "ideation"
        # 确认状态已更新
        state = json.loads((tmp_path / "project_state.json").read_text(encoding="utf-8"))
        assert state["current_stage"] == "ideation"
        assert len(state["rollback_history"]) == 1

    def test_rollback_no_target(self, tmp_path):
        _write_json(tmp_path, "project_state.json", {
            "current_stage": "survey_search",
        })
        from server import complete_stage
        result = complete_stage(str(tmp_path), "survey_search", result="rollback")
        assert result["status"] == "error"

    def test_advance_to_next(self, tmp_path):
        _write_json(tmp_path, "project_state.json", {
            "current_stage": "insight_interview",
            "user_level": "novice",
            "target_venue": "NeurIPS",
        })
        from server import complete_stage
        result = complete_stage(str(tmp_path), "insight_interview")
        assert result["status"] == "advanced"
        assert result["next"]["stage_name"] == "survey_search"


class TestReenterPipeline:

    def test_reenter(self, tmp_path):
        _write_json(tmp_path, "project_state.json", {
            "current_stage": None,
            "stages_completed": list(STAGE_ORDER),
        })
        from server import reenter_pipeline
        result = reenter_pipeline(str(tmp_path), "experiment_run")
        assert result["status"] == "reentered"
        assert result["reentry_stage"] == "experiment_run"
        state = json.loads((tmp_path / "project_state.json").read_text(encoding="utf-8"))
        assert state["current_stage"] == "experiment_run"

    def test_reenter_with_feedback(self, tmp_path):
        _write_json(tmp_path, "project_state.json", {"current_stage": None})
        from server import reenter_pipeline
        result = reenter_pipeline(str(tmp_path), "writing", "reviews.md")
        assert result["reviewer_feedback"] == "reviews.md"

    def test_reenter_invalid_stage(self, tmp_path):
        from server import reenter_pipeline
        result = reenter_pipeline(str(tmp_path), "nonexistent")
        assert result["status"] == "error"


class TestGetPipelineStatus:

    def test_initial(self, tmp_path):
        from server import get_pipeline_status
        result = get_pipeline_status(str(tmp_path))
        assert result["current_stage"] == "insight_interview"
        assert len(result["stages"]) == 18
        assert result["user_level"] == "intermediate"

    def test_has_rollback_info(self, tmp_path):
        from server import get_pipeline_status
        result = get_pipeline_status(str(tmp_path))
        has_rollback = [s for s in result["stages"] if s.get("has_rollback")]
        assert len(has_rollback) == 4


# ============================================================
# 3-Round Review Chain
# ============================================================


class TestReviewChain:

    def test_review_round1_to_revise_round1(self):
        s = get_stage("review_round1")
        assert s.next_stage == "revise_round1"

    def test_revise_round1_to_review_round2(self):
        s = get_stage("revise_round1")
        assert s.next_stage == "review_round2"

    def test_review_round2_to_revise_round2(self):
        s = get_stage("review_round2")
        assert s.next_stage == "revise_round2"

    def test_revise_round2_to_meta_review(self):
        s = get_stage("revise_round2")
        assert s.next_stage == "review_round3_meta"

    def test_meta_review_to_final_revise(self):
        s = get_stage("review_round3_meta")
        assert s.next_stage == "final_revise"

    def test_meta_review_can_rollback(self):
        rb = get_rollback_stage("review_round3_meta")
        assert rb.name == "experiment_run"


# ============================================================
# v2.2: Anti-pattern + Soft Quality Tests
# ============================================================


class TestAntiPatternDetection:

    def test_ai_opening_detected(self, tmp_path):
        _write_text(tmp_path, "artifacts/draft_final.tex",
                    "In recent years, deep learning has attracted...")
        _write_json(tmp_path, "artifacts/story_skeleton.json", {})
        errors = validate_stage("writing", str(tmp_path))
        assert any("AI 典型表达" in e for e in errors)

    def test_no_figure_warning(self, tmp_path):
        _write_text(tmp_path, "artifacts/draft_final.tex",
                    "\\documentclass{article}\n\\begin{document}\nHello\\end{document}")
        _write_json(tmp_path, "artifacts/story_skeleton.json", {})
        errors = validate_stage("writing", str(tmp_path))
        assert any("Figure 1" in e for e in errors)

    def test_missing_one_sentence_summary(self, tmp_path):
        _write_text(tmp_path, "artifacts/draft_final.tex",
                    "\\begin{figure}\\end{figure}")
        _write_json(tmp_path, "artifacts/story_skeleton.json", {
            "weakness_preemption": [{"attack": "x", "defense": "y"}]
        })
        errors = validate_stage("writing", str(tmp_path))
        assert any("one_sentence_summary" in e for e in errors)

    def test_missing_weakness_preemption(self, tmp_path):
        _write_text(tmp_path, "artifacts/draft_final.tex",
                    "\\begin{figure}\\end{figure}")
        _write_json(tmp_path, "artifacts/story_skeleton.json", {
            "one_sentence_summary": "We show X improves Y by Z."
        })
        errors = validate_stage("writing", str(tmp_path))
        assert any("weakness_preemption" in e for e in errors)

    def test_writing_pass_with_full_skeleton(self, tmp_path):
        tex = (
            "\\section{Introduction}\n\n"
            "To address X, we propose Y. Improves by 5% because Z.\n\n"
            "Unlike prior work, our approach results in better generalization.\n\n"
            "\\section{Method}\n\n"
            "To overcome A:\n"
            "\\begin{equation} L = L_1 \\end{equation}\n\n"
            "Allows us to model structure. Compared to B, reduces by 10%.\n\n"
            "\\section{Experiments}\n\n"
            "\\subsection{Setup}\nDetails.\n\n"
            "\\subsection{Main Results}\n"
            "\\begin{figure}\\caption{Overview}\\end{figure}\n"
            "achieves 92.3% accuracy.\n\n"
            "\\subsection{Ablation}\nablation component analysis\n\n"
            "\\subsection{Analysis}\ncase study qualitative visualization\n\n"
            "\\subsection{Limitation}\nfailure limitation\n\n"
            "sensitivity robustness efficiency speed\n\n"
        )
        _write_text(tmp_path, "artifacts/draft_final.tex", tex)
        _write_json(tmp_path, "artifacts/story_skeleton.json", {
            "one_sentence_summary": "We show X.",
            "weakness_preemption": [{"attack": "a", "defense": "d"}],
            "contributions": ["Overview"],
        })
        errors = validate_stage("writing", str(tmp_path))
        assert errors == []

    def test_writing_stage_has_persuasion(self):
        s = get_stage("writing")
        assert "Weakness Preemption" in s.instructions
        assert "Figure 1" in s.instructions
        assert "One-Sentence" in s.instructions
        assert "Narrative Momentum" in s.instructions
        assert "Rebuttal" in s.instructions

    def test_venue_fit_has_positioning(self):
        s = get_stage("venue_fit_check")
        assert "Positioning Strategy" in s.instructions
        assert "Significance Argument" in s.instructions


# ============================================================
# v3: Schema Validation
# ============================================================


class TestSchemaValidation:

    def test_evidence_graph_schema_pass(self, tmp_path):
        _write_json(tmp_path, "evidence_graph.json", {
            "claims": [
                {"id": f"c{i}", "type": "method", "text": f"Claim {i}",
                 "source_paper_id": f"p{i}", "exact_quote": "", "confidence": 0.9}
                for i in range(10)
            ]
        })
        _write_text(tmp_path, "artifacts/survey.md")
        assert validate_stage("survey_fetch", str(tmp_path)) == []

    def test_evidence_graph_schema_fail(self, tmp_path):
        # Missing required 'type' field in claim
        _write_json(tmp_path, "evidence_graph.json", {
            "claims": [{"id": "c1", "text": "test", "source_paper_id": "p1"}]
        })
        _write_text(tmp_path, "artifacts/survey.md")
        errors = validate_stage("survey_fetch", str(tmp_path))
        assert any("Schema" in e or "schema" in e.lower() or "type" in e.lower() for e in errors)

    def test_project_state_schema_pass(self, tmp_path):
        _write_json(tmp_path, "project_state.json", {
            "user_level": "expert",
            "target_venue": "NeurIPS",
            "autopilot": False,
        })
        errors = validate_stage("insight_interview", str(tmp_path))
        assert errors == []


# ============================================================
# v3: recover_pipeline
# ============================================================


class TestRecoverPipeline:

    def test_recover_from_clean_start(self, tmp_path):
        from server import recover_pipeline
        result = recover_pipeline(str(tmp_path))
        assert result["status"] == "recovered"
        assert result["current_stage"] == "insight_interview"

    def test_recover_with_partial_progress(self, tmp_path):
        # Stage 1 done: insight_interview
        _write_json(tmp_path, "project_state.json", {
            "current_stage": "survey_fetch",  # stale
            "user_level": "expert",
            "target_venue": "ICML",
            "stages_completed": [],
        })
        from server import recover_pipeline
        result = recover_pipeline(str(tmp_path))
        assert result["status"] == "recovered"
        assert "insight_interview" in result["actual_completed"]
        # survey_search 没有产出，所以应停在这里
        assert result["current_stage"] == "survey_search"

    def test_recover_preserves_existing(self, tmp_path):
        _write_json(tmp_path, "project_state.json", {
            "current_stage": None,
            "user_level": "intermediate",
            "target_venue": "NeurIPS",
            "rollback_history": [{"from": "x", "to": "y"}],
        })
        from server import recover_pipeline
        result = recover_pipeline(str(tmp_path))
        # State should be recovered but existing fields preserved
        state = json.loads((tmp_path / "project_state.json").read_text(encoding="utf-8"))
        assert len(state["rollback_history"]) == 1


# ============================================================
# v3: log_decision + context_summary
# ============================================================


class TestDecisionLog:

    def test_log_decision(self, tmp_path):
        from server import log_decision
        result = log_decision(
            str(tmp_path), "ideation", "选择 idea-003",
            "可行性最高", ["idea-001", "idea-005"]
        )
        assert result["status"] == "logged"
        assert result["total_decisions"] == 1

    def test_log_multiple_decisions(self, tmp_path):
        from server import log_decision
        log_decision(str(tmp_path), "ideation", "选择 idea-003")
        log_decision(str(tmp_path), "novelty_check", "继续，接受中等风险")
        result = log_decision(str(tmp_path), "experiment_design", "用 Type A 模板")
        assert result["total_decisions"] == 3

    def test_context_summary_in_advance(self, tmp_path):
        from server import log_decision, advance_pipeline
        _write_json(tmp_path, "project_state.json", {
            "current_stage": "ideation",
            "user_level": "expert",
            "target_venue": "NeurIPS",
            "stages_completed": [
                "insight_interview", "survey_search", "survey_fetch",
                "evidence_audit",
            ],
        })
        log_decision(str(tmp_path), "survey", "关注 GNN 方向")
        result = advance_pipeline(str(tmp_path))
        assert "context_summary" in result
        assert result["context_summary"]["user_level"] == "expert"
        assert result["context_summary"]["target_venue"] == "NeurIPS"
        assert len(result["context_summary"]["recent_decisions"]) == 1

    def test_context_summary_includes_selected_idea(self, tmp_path):
        _write_json(tmp_path, "project_state.json", {
            "current_stage": "deep_dive",
            "stages_completed": [
                "insight_interview", "survey_search", "survey_fetch",
                "evidence_audit", "ideation",
            ],
        })
        _write_json(tmp_path, "hypothesis_board.json", {
            "hypotheses": [
                {"id": "h1", "title": "My Cool Idea", "selected": True},
                {"id": "h2", "title": "Another Idea", "selected": False},
            ]
        })
        from server import advance_pipeline
        result = advance_pipeline(str(tmp_path))
        assert result["context_summary"]["selected_idea"] == "My Cool Idea"


# ============================================================
# v3: Integrity Check
# ============================================================


class TestIntegrityCheck:

    def test_integrity_warning_on_skip(self, tmp_path):
        # current_stage is survey_fetch but survey_search not completed
        _write_json(tmp_path, "project_state.json", {
            "current_stage": "survey_fetch",
            "stages_completed": [],
        })
        from server import advance_pipeline
        result = advance_pipeline(str(tmp_path))
        assert result["status"] == "integrity_warning"
        assert "survey_search" in result["message"]

    def test_no_integrity_warning_after_rollback(self, tmp_path):
        _write_json(tmp_path, "project_state.json", {
            "current_stage": "ideation",
            "stages_completed": [],
            "rollback_history": [{"from": "novelty_check", "to": "ideation"}],
        })
        from server import advance_pipeline
        result = advance_pipeline(str(tmp_path))
        assert result["status"] != "integrity_warning"


# ============================================================
# v3: Stage Timeout
# ============================================================


class TestStageTimeout:

    def test_stage_max_hours_defined(self):
        assert get_stage("insight_interview").max_hours == 2.0
        assert get_stage("experiment_run").max_hours == 72.0

    def test_default_max_hours(self):
        assert get_stage("venue_fit_check").max_hours == 24.0

    def test_timeout_detection(self, tmp_path):
        from datetime import timedelta
        from datetime import datetime, timezone
        _write_json(tmp_path, "project_state.json", {
            "current_stage": "insight_interview",
            "stages_completed": [],
            # Set start time 3 hours ago (exceeds 2h limit)
            "stage_start_time": (
                datetime.now(timezone.utc) - timedelta(hours=3)
            ).isoformat(),
        })
        from server import advance_pipeline
        result = advance_pipeline(str(tmp_path))
        assert result["status"] == "timeout_warning"
        assert "2.0" in str(result["max_hours"])


# ============================================================
# v3: SDP Mode
# ============================================================


class TestSdpMode:

    def test_sdp_mode_in_advance(self, tmp_path):
        _write_json(tmp_path, "project_state.json", {
            "current_stage": "ideation",
            "sdp_mode": "lite",
            "stages_completed": [
                "insight_interview", "survey_search", "survey_fetch",
                "evidence_audit",
            ],
        })
        from server import advance_pipeline
        result = advance_pipeline(str(tmp_path))
        assert result["sdp_mode"] == "lite"
        assert "Lite" in result.get("model_switch_note", "")

    def test_same_model_mode(self, tmp_path):
        _write_json(tmp_path, "project_state.json", {
            "current_stage": "ideation",
            "sdp_mode": "same_model",
            "stages_completed": [
                "insight_interview", "survey_search", "survey_fetch",
                "evidence_audit",
            ],
        })
        from server import advance_pipeline
        result = advance_pipeline(str(tmp_path))
        assert "Same-Model" in result.get("model_switch_note", "")


# ============================================================
# v3: End-to-End Integration
# ============================================================


def _setup_stage_outputs(tmp: Path, stage: str) -> None:
    """为指定 stage 创建能通过 validator 的最小产出。"""
    if stage == "insight_interview":
        _write_json(tmp, "project_state.json", {
            "user_level": "expert", "target_venue": "NeurIPS",
            "current_stage": "insight_interview",
        })
    elif stage == "survey_search":
        _write_json(tmp, "corpus_ledger.json", {"entries": [{"id": "p1", "title": "Paper 1"}]})
    elif stage == "survey_fetch":
        _write_json(tmp, "evidence_graph.json", {
            "claims": [{"id": f"c{i}", "type": "method", "text": f"Claim {i}",
                        "source_paper_id": f"p{i}"} for i in range(10)]
        })
        _write_text(tmp, "artifacts/survey.md")
    elif stage == "evidence_audit":
        _write_text(tmp, "evidence_audit.md")
    elif stage == "ideation":
        _write_json(tmp, "hypothesis_board.json", {
            "hypotheses": [{"id": "h1", "title": "Test Idea", "selected": True,
                            "contribution_delta": {
                                "delta_method": {"score": 4}, "delta_performance": {"score": 3},
                                "delta_scope": {"score": 3}, "delta_insight": {"score": 4}}}]
        })
        # Compliance artifacts
        _write_text(tmp, "dialogue/frontier_analysis.md", "frontier")
        _write_text(tmp, "dialogue/tot_survivors.md", "survivors")
        _write_text(tmp, "dialogue/benchmark_analysis.md", "benchmark")
        _write_text(tmp, "dialogue/red_team_report.md", "red team")
        _write_text(tmp, "dialogue/ideas_v2.md", "ideas v2")
    elif stage == "deep_dive":
        _write_text(tmp, "artifacts/deep_dive_paper1.md")
    elif stage == "novelty_check":
        _write_json(tmp, "hypothesis_board.json", {
            "hypotheses": [{"id": "h1", "selected": True,
                            "novelty_risk": {"overall_risk": "low",
                                             "total_papers_scanned": 50}}]
        })
    elif stage == "experiment_design":
        _write_text(tmp, "experimental_design.md")
    elif stage == "pilot_experiment":
        _write_json(tmp, "artifacts/pilot_results.json", {"status": "pass"})
    elif stage == "experiment_run":
        _write_text(tmp, "artifacts/experiment_report.md")
        _write_json(tmp, "artifacts/experiment_results.json", {
            "main_table": [{"name": "acc", "value": 0.95, "std": 0.01, "num_seeds": 3}]
        })
        # Compliance artifacts
        _write_text(tmp, "artifacts/code_audit.md", "audit")
        _write_text(tmp, "artifacts/experiment_story.md", "story")
        _write_text(tmp, "artifacts/baseline_verification.md", "baseline")
    elif stage == "venue_fit_check":
        _write_text(tmp, "artifacts/venue_fit_report.md")
    elif stage == "writing":
        tex = (
            "\\section{Introduction}\n\n"
            "To address X, we propose Y. Improves by 5% because Z.\n\n"
            "Unlike prior work, our approach results in better generalization.\n\n"
            "\\section{Method}\n\n"
            "To overcome A, we define:\n"
            "\\begin{equation} L = L_1 \\end{equation}\n\n"
            "This allows us to model structure. Compared to B, reduces by 10%.\n\n"
            "\\section{Experiments}\n\n"
            "\\subsection{Setup}\nDetails.\n\n"
            "\\subsection{Main Results}\n"
            "\\begin{figure}\\caption{Overview}\\end{figure}\n"
            "achieves 92.3% accuracy.\n\n"
            "\\subsection{Ablation}\nablation component analysis\n\n"
            "\\subsection{Analysis}\ncase study qualitative visualization\n\n"
            "\\subsection{Limitation}\nfailure limitation\n\n"
            "sensitivity robustness efficiency speed\n\n"
        )
        _write_text(tmp, "artifacts/draft_final.tex", tex)
        _write_json(tmp, "artifacts/story_skeleton.json", {
            "one_sentence_summary": "We show X.",
            "weakness_preemption": [{"attack": "a", "defense": "d"}],
            "contributions": ["Overview"],
        })
        # Compliance artifacts
        _write_text(tmp, "artifacts/exemplar_analysis.md", "exemplar")
        _write_text(tmp, "artifacts/fresh_eyes_result.md", "fresh eyes")
    elif stage in ("review_round1", "review_round2"):
        _write_json(tmp, f"artifacts/{stage}.json", {"reviews": []})
        if stage == "review_round1":
            # Compliance artifacts
            _write_text(tmp, "dialogue/rejection_preview.md", "preview")
            _write_text(tmp, "dialogue/reviews_gemini.md", "R-A/B/C")
            _write_text(tmp, "dialogue/reviews_gpt.md", "R-D/E/F")
            _write_text(tmp, "dialogue/cross_review_gemini.md", "cross")
    elif stage in ("revise_round1", "revise_round2"):
        _write_text(tmp, "artifacts/draft_final.tex")
    elif stage == "review_round3_meta":
        _write_json(tmp, "artifacts/meta_review.json", {"decision": "accept"})
    elif stage == "final_revise":
        _write_text(tmp, "artifacts/draft_final.tex", "\\documentclass{article}")
        _write_text(tmp, "artifacts/reproducibility_checklist.md")


class TestEndToEndPipeline:
    """端到端 pipeline 路径测试。"""

    def test_happy_path_first_three_stages(self, tmp_path):
        """insight → survey_search → survey_fetch 连续推进。"""
        from server import advance_pipeline, complete_stage

        # Initial: should be insight_interview
        r = advance_pipeline(str(tmp_path))
        assert r["stage_name"] == "insight_interview"

        # Set up and complete insight_interview
        _setup_stage_outputs(tmp_path, "insight_interview")
        r = complete_stage(str(tmp_path), "insight_interview")
        assert r["status"] == "advanced"
        assert r["next"]["stage_name"] == "survey_search"

        # Set up and complete survey_search
        _setup_stage_outputs(tmp_path, "survey_search")
        r = complete_stage(str(tmp_path), "survey_search")
        assert r["status"] == "advanced"
        assert r["next"]["stage_name"] == "survey_fetch"

    def test_rollback_then_resume(self, tmp_path):
        """pilot 失败 → rollback 到 ideation → 换 idea → 重新走。"""
        from server import complete_stage

        _write_json(tmp_path, "project_state.json", {
            "current_stage": "pilot_experiment",
            "stages_completed": [
                "insight_interview", "survey_search", "survey_fetch",
                "evidence_audit", "ideation", "deep_dive", "novelty_check",
                "experiment_design",
            ],
            "user_level": "expert",
            "target_venue": "NeurIPS",
        })

        # Rollback from pilot
        r = complete_stage(str(tmp_path), "pilot_experiment", result="rollback")
        assert r["status"] == "rolled_back"
        assert r["to_stage"] == "ideation"

        # Complete ideation again with new idea
        _setup_stage_outputs(tmp_path, "ideation")
        r = complete_stage(str(tmp_path), "ideation")
        assert r["status"] == "advanced"
        assert r["next"]["stage_name"] == "deep_dive"

    def test_double_rollback(self, tmp_path):
        """pilot rollback + experiment_run rollback 连续发生。"""
        from server import complete_stage

        # First rollback: pilot → ideation
        _write_json(tmp_path, "project_state.json", {
            "current_stage": "pilot_experiment",
            "stages_completed": [
                "insight_interview", "survey_search", "survey_fetch",
                "evidence_audit", "ideation", "deep_dive", "novelty_check",
                "experiment_design",
            ],
        })
        r = complete_stage(str(tmp_path), "pilot_experiment", result="rollback")
        assert r["status"] == "rolled_back"
        assert r["to_stage"] == "ideation"
        state = json.loads((tmp_path / "project_state.json").read_text(encoding="utf-8"))
        assert len(state["rollback_history"]) == 1

        # Walk back to experiment_run
        _setup_stage_outputs(tmp_path, "ideation")
        complete_stage(str(tmp_path), "ideation")
        _setup_stage_outputs(tmp_path, "deep_dive")
        complete_stage(str(tmp_path), "deep_dive")
        _setup_stage_outputs(tmp_path, "novelty_check")
        complete_stage(str(tmp_path), "novelty_check")
        _setup_stage_outputs(tmp_path, "experiment_design")
        complete_stage(str(tmp_path), "experiment_design")
        _setup_stage_outputs(tmp_path, "pilot_experiment")
        complete_stage(str(tmp_path), "pilot_experiment")

        # Second rollback: experiment_run → experiment_design
        r = complete_stage(str(tmp_path), "experiment_run", result="rollback")
        assert r["status"] == "rolled_back"
        assert r["to_stage"] == "experiment_design"

        state = json.loads((tmp_path / "project_state.json").read_text(encoding="utf-8"))
        assert len(state["rollback_history"]) == 2

    def test_reenter_after_full_completion(self, tmp_path):
        """Pipeline 完成后 reenter 到 writing 带 reviewer feedback。"""
        from server import reenter_pipeline, advance_pipeline

        _write_json(tmp_path, "project_state.json", {
            "current_stage": None,
            "stages_completed": list(STAGE_ORDER),
        })

        r = reenter_pipeline(str(tmp_path), "writing", "reviews_real.md")
        assert r["status"] == "reentered"
        assert r["reentry_stage"] == "writing"
        assert r["reviewer_feedback"] == "reviews_real.md"

        # Should be able to advance from writing
        r = advance_pipeline(str(tmp_path))
        assert r["stage_name"] == "writing"

    def test_recover_from_interruption(self, tmp_path):
        """模拟中断后 recover_pipeline 正确推断进度。"""
        from server import recover_pipeline

        # Set up: insight_interview is done
        _setup_stage_outputs(tmp_path, "insight_interview")
        _setup_stage_outputs(tmp_path, "survey_search")
        # survey_fetch is NOT done (no evidence_graph)

        # Corrupt state: claims wrong stage
        _write_json(tmp_path, "project_state.json", {
            "current_stage": "ideation",  # wrong!
            "user_level": "expert",
            "target_venue": "NeurIPS",
            "stages_completed": ["insight_interview", "survey_search", "survey_fetch"],
        })

        r = recover_pipeline(str(tmp_path))
        assert r["status"] == "recovered"
        # insight_interview should pass (project_state has user_level + venue)
        assert "insight_interview" in r["actual_completed"]
        # survey_search should pass (corpus_ledger exists)
        assert "survey_search" in r["actual_completed"]
        # survey_fetch should fail (no evidence_graph with enough claims)
        assert r["current_stage"] == "survey_fetch"

