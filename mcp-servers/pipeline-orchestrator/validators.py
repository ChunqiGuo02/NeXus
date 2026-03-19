"""Pipeline 产出验证器 v3 — schema 验证 + 内容级语义检查 + venue playbook 联动。

从 v2 升级：
- 所有 JSON 加载先经 Pydantic schema 验证
- validate_final_revise 从 venue playbook 读取 venue 特定规则
- 统计严谨性（multi-seed, error bars）
- Ablation 完整性 / Baseline 时效性
- Claims↔Paper 交叉验证 + Overclaiming
- Pre-submission compliance + 引用一致性
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from schemas import (
    CorpusLedger,
    EvidenceGraph,
    HypothesisBoard,
    ProjectState,
    validate_json_schema,
)


def _file_exists(project_dir: str, rel_path: str) -> bool:
    return (Path(project_dir) / rel_path).exists()


def _load_json(project_dir: str, rel_path: str) -> dict | list | None:
    p = Path(project_dir) / rel_path
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _read_text(project_dir: str, rel_path: str) -> str | None:
    p = Path(project_dir) / rel_path
    if not p.exists():
        return None
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return None


def _load_venue_playbook(venue: str) -> dict | None:
    """从 venue_playbooks/playbooks.json 加载指定 venue 的配置。"""
    playbooks_path = Path(__file__).parent / "venue_playbooks" / "playbooks.json"
    if not playbooks_path.exists():
        return None
    try:
        data = json.loads(playbooks_path.read_text(encoding="utf-8"))
        venues = data if isinstance(data, list) else data.get("venues", [])
        for v in venues:
            if v.get("venue", "").lower() == venue.lower():
                return v
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _estimate_pages(tex: str) -> int | None:
    """粗略估算 LaTeX 页数（约 3000 字符/页）。"""
    # 去掉注释和 preamble
    content = re.sub(r'%.*$', '', tex, flags=re.MULTILINE)
    body_match = re.search(r'\\begin\{document\}(.*)\\end\{document\}', content, re.DOTALL)
    if body_match:
        content = body_match.group(1)
    # 去掉 LaTeX 命令，粗略估算
    text_only = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', content)
    text_only = re.sub(r'\\[a-zA-Z]+', '', text_only)
    char_count = len(text_only.strip())
    if char_count < 100:
        return None
    return max(1, char_count // 3000)


# ---------- Stage Validators ---------- #


def validate_insight_interview(project_dir: str) -> list[str]:
    """insight_interview: project_state.json 必须包含 user_level。"""
    missing = []
    data = _load_json(project_dir, "project_state.json")
    if data is None:
        missing.append("project_state.json 不存在")
        return missing
    # Schema 验证
    schema_errors = validate_json_schema(data, ProjectState)
    if schema_errors:
        missing.extend(schema_errors)
        return missing
    if isinstance(data, dict):
        if not data.get("user_level"):
            missing.append("project_state.json 缺少 user_level 字段")
        if not data.get("target_venue"):
            missing.append("project_state.json 缺少 target_venue 字段")
    return missing


def validate_survey_search(project_dir: str) -> list[str]:
    """survey_search: corpus_ledger.json 必须存在且至少有 1 篇论文。"""
    missing = []
    data = _load_json(project_dir, "corpus_ledger.json")
    if data is None:
        missing.append("corpus_ledger.json 不存在或格式错误")
        return missing
    schema_errors = validate_json_schema(data, CorpusLedger)
    if schema_errors:
        missing.extend(schema_errors)
        return missing
    if isinstance(data, dict):
        entries = data.get("entries", [])
        if len(entries) < 1:
            missing.append("corpus_ledger.json 中无论文条目")
    return missing


def validate_survey_fetch(project_dir: str) -> list[str]:
    """survey_fetch: evidence_graph 至少 10 条 claims + survey.md 存在。"""
    missing = []
    data = _load_json(project_dir, "evidence_graph.json")
    if data is None:
        missing.append("evidence_graph.json 不存在或格式错误")
        return missing
    schema_errors = validate_json_schema(data, EvidenceGraph)
    if schema_errors:
        missing.extend(schema_errors)
        return missing
    if isinstance(data, dict):
        claims = data.get("claims", [])
        if len(claims) < 10:
            missing.append(
                f"evidence_graph.json 中 claims 不足 10 条（当前 {len(claims)} 条）"
            )
    if not _file_exists(project_dir, "artifacts/survey.md"):
        missing.append("artifacts/survey.md 不存在")
    return missing


def validate_evidence_audit(project_dir: str) -> list[str]:
    """evidence_audit: 审计报告必须存在。"""
    missing = []
    if not _file_exists(project_dir, "evidence_audit.md"):
        missing.append("evidence_audit.md 不存在")
    return missing


def validate_domain_calibration(project_dir: str) -> list[str]:
    """domain_calibration: 自动领域品味学习是否完成。"""
    missing = []

    taste = _load_json(project_dir, "artifacts/domain_taste_profile.json")
    if taste is None:
        missing.append("artifacts/domain_taste_profile.json 不存在")
        return missing

    # 样本量检查
    if isinstance(taste, dict):
        samples = taste.get("sample_sizes", {})
        if samples.get("tier1_elite", 0) < 5:
            missing.append(
                "Tier-1 Elite 样本不足 5 篇 — 品味学习数据不充分"
            )
        if samples.get("tier1_poster", 0) < 5:
            missing.append(
                "Tier-1 Poster 样本不足 5 篇"
            )

        # 阶梯差异存在性
        norms = taste.get("structural_norms", {})
        if not norms:
            missing.append("structural_norms 为空 — 差异分析未完成")

        # 写作规则
        rules = taste.get("concrete_writing_rules", [])
        if len(rules) < 3:
            missing.append(
                "concrete_writing_rules 不足 3 条 — 规则提炼不充分"
            )

    if not _file_exists(project_dir, "artifacts/exemplar_structures.json"):
        missing.append(
            "artifacts/exemplar_structures.json 不存在 — 范例结构未提取"
        )

    return missing


def validate_ideation(project_dir: str) -> list[str]:
    """ideation: hypothesis_board 必须有至少 1 个选定 idea。"""
    missing = []
    data = _load_json(project_dir, "hypothesis_board.json")
    if data is None:
        missing.append("hypothesis_board.json 不存在或格式错误")
        return missing
    schema_errors = validate_json_schema(data, HypothesisBoard)
    if schema_errors:
        missing.extend(schema_errors)
        return missing
    if isinstance(data, dict):
        hypotheses = data.get("hypotheses", [])
        selected = [h for h in hypotheses if h.get("selected")]
        if not selected:
            missing.append("hypothesis_board.json 中无选定的 idea")
        # v4: Contribution Magnitude Gate (CMG)
        for h in selected:
            cd = h.get("contribution_delta", {})
            if not cd:
                missing.append(
                    "⚠️ 选定 idea 缺少 contribution_delta 四维评估"
                )
            else:
                scores = [
                    cd.get(k, {}).get("score", 0)
                    for k in [
                        "delta_method", "delta_performance",
                        "delta_scope", "delta_insight",
                    ]
                ]
                high_dims = sum(1 for s in scores if s >= 3)
                insight = cd.get(
                    "delta_insight", {}
                ).get("score", 0)
                if high_dims <= 1:
                    missing.append(
                        f"⛔ Contribution Magnitude 不足：仅 "
                        f"{high_dims}/4 维度 ≥3。"
                        f"Idea 可能是 incremental。"
                    )
                elif insight < 3:
                    missing.append(
                        f"⚠️ delta_insight 不足"
                        f"（score={insight}）。"
                        f"缺乏新发现的论文容易被拒。"
                    )
    return missing


def validate_deep_dive(project_dir: str) -> list[str]:
    """deep_dive: 至少 1 个精读笔记存在。"""
    missing = []
    artifacts = Path(project_dir) / "artifacts"
    if not artifacts.exists():
        missing.append("artifacts/ 目录不存在")
        return missing
    deep_dive_files = list(artifacts.glob("deep_dive_*.md"))
    if not deep_dive_files:
        missing.append("无 artifacts/deep_dive_*.md 精读笔记")
    return missing


def validate_novelty_check(project_dir: str) -> list[str]:
    """novelty_check: 选定 idea 必须有 novelty_risk 字段。"""
    missing = []
    data = _load_json(project_dir, "hypothesis_board.json")
    if data is None:
        missing.append("hypothesis_board.json 不存在或格式错误")
        return missing
    if isinstance(data, dict):
        hypotheses = data.get("hypotheses", [])
        selected = [h for h in hypotheses if h.get("selected")]
        for h in selected:
            if "novelty_risk" not in h:
                missing.append(f"idea '{h.get('id', '?')}' 缺少 novelty_risk 字段")
    return missing


def validate_experiment_design(project_dir: str) -> list[str]:
    """experiment_design: design 存在 + baseline 时效性 + ablation 计划。"""
    missing = []
    if not _file_exists(project_dir, "experimental_design.md"):
        missing.append("experimental_design.md 不存在")
        return missing

    # v2: Baseline 时效性检查（如有结构化数据）
    design = _load_json(project_dir, "experimental_design.json")
    if design and isinstance(design, dict):
        import datetime as dt
        current_year = dt.datetime.now().year
        for baseline in design.get("baselines", []):
            year = baseline.get("year", 0)
            if year and current_year - year > 2:
                missing.append(
                    f"⚠️ Baseline '{baseline.get('name', '?')}' 发表于 {year}，"
                    f"建议补充 {current_year - 1}-{current_year} 的 baseline"
                )

        # Ablation 计划
        components = design.get("novel_components", [])
        ablations = design.get("ablation_plan", [])
        for comp in components:
            comp_name = comp if isinstance(comp, str) else comp.get("name", "?")
            if not any(comp_name in str(a) for a in ablations):
                missing.append(f"缺少 novel component '{comp_name}' 的 ablation 计划")
    return missing


def validate_pilot_experiment(project_dir: str) -> list[str]:
    """pilot_experiment: pilot 结果必须存在。"""
    missing = []
    data = _load_json(project_dir, "artifacts/pilot_results.json")
    if data is None:
        missing.append("artifacts/pilot_results.json 不存在或格式错误")
    return missing


def validate_experiment_run(project_dir: str) -> list[str]:
    """experiment_run: 实验报告 + 统计严谨性 + ablation 完整性。"""
    missing = []
    if not _file_exists(project_dir, "artifacts/experiment_report.md"):
        missing.append("artifacts/experiment_report.md 不存在")

    # v2: 统计严谨性检查
    results = _load_json(project_dir, "artifacts/experiment_results.json")
    if results is None:
        missing.append("artifacts/experiment_results.json 不存在")
        return missing

    if isinstance(results, dict):
        # 多 seed 检查
        for metric in results.get("main_table", []):
            num_seeds = metric.get("num_seeds", 1)
            if num_seeds < 3:
                missing.append(
                    f"指标 '{metric.get('name', '?')}' 仅 {num_seeds} 个 seed，需 ≥3"
                )
            if "std" not in metric and num_seeds >= 3:
                missing.append(f"指标 '{metric.get('name', '?')}' 缺少 std")

        # Ablation 完整性
        design = _load_json(project_dir, "experimental_design.json")
        if design and isinstance(design, dict):
            components = design.get("novel_components", [])
            ablation_results = results.get("ablation_table", [])
            ablation_names = [str(a.get("name", a)) for a in ablation_results] \
                if isinstance(ablation_results, list) else []
            for comp in components:
                comp_name = comp if isinstance(comp, str) else comp.get("name", "?")
                if not any(comp_name.lower() in name.lower() for name in ablation_names):
                    missing.append(f"缺少 '{comp_name}' 的 ablation 实验结果")

    return missing


def validate_venue_fit_check(project_dir: str) -> list[str]:
    """venue_fit_check: venue fit 报告必须存在。"""
    missing = []
    if not _file_exists(project_dir, "artifacts/venue_fit_report.md"):
        missing.append("artifacts/venue_fit_report.md 不存在")
    return missing


def validate_writing(project_dir: str) -> list[str]:
    """writing: draft + story_skeleton + claims 交叉验证。"""
    missing = []
    if not _file_exists(project_dir, "artifacts/draft_final.tex"):
        missing.append("artifacts/draft_final.tex 不存在")
    if not _file_exists(project_dir, "artifacts/story_skeleton.json"):
        missing.append("artifacts/story_skeleton.json 不存在")

    # v2: Claims↔Paper 交叉验证（基础版：检查 evidence_graph 引用）
    tex = _read_text(project_dir, "artifacts/draft_final.tex")
    evidence = _load_json(project_dir, "evidence_graph.json")
    if tex and evidence and isinstance(evidence, dict):
        # Shadow source 检查
        ledger = _load_json(project_dir, "corpus_ledger.json")
        if ledger and isinstance(ledger, dict):
            cite_keys = set(re.findall(r'\\cite\{([^}]+)\}', tex))
            expanded = set()
            for group in cite_keys:
                expanded.update(k.strip() for k in group.split(","))
            for entry in ledger.get("entries", []):
                eid = entry.get("cite_key", entry.get("id", ""))
                if eid in expanded and entry.get("publishable") is False:
                    missing.append(
                        f"引用 '{eid}' 标记为 publishable=false（shadow source 泄露）"
                    )

    # v2.2: Anti-pattern 硬规则（必拒模式检测）
    if tex:
        # AI 典型开头
        ai_openings = [
            r"In recent years",
            r"In the era of",
            r"With the rapid development",
            r"has attracted considerable attention",
            r"has garnered significant interest",
        ]
        for pattern in ai_openings:
            if re.search(pattern, tex, re.IGNORECASE):
                missing.append(
                    f"⚠️ AI 典型表达检测: '{pattern}' — 建议用具体问题切入"
                )

        # Figure 1 存在性
        if not re.search(r'\\begin\{figure\}', tex):
            missing.append("⚠️ 论文中无 figure 环境 — 缺少 Figure 1 方法概览图")

    # v2.2: story_skeleton 软质量检查
    skeleton = _load_json(project_dir, "artifacts/story_skeleton.json")
    if skeleton and isinstance(skeleton, dict):
        if not skeleton.get("one_sentence_summary"):
            missing.append(
                "⚠️ story_skeleton.json 缺少 one_sentence_summary"
                "（论文缺焦点）"
            )
        if not skeleton.get("weakness_preemption"):
            missing.append(
                "⚠️ story_skeleton.json 缺少 weakness_preemption"
                "（主动防御计划）"
            )

    # v4: Experiment Story Arc
    if tex:
        story_arc = {
            "why_it_works": [
                "ablation", "ablat", "component analysis",
                "contribution of", "effect of",
            ],
            "deep_analysis": [
                "case study", "error analysis",
                "qualitative", "visualization",
            ],
            "when_it_fails": [
                "failure", "limitation", "fails",
                "does not work", "struggles with",
            ],
        }
        for name, markers in story_arc.items():
            if not any(m in tex.lower() for m in markers):
                missing.append(
                    f"⚠️ Experiment section 缺少 "
                    f"'{name}' 段。"
                    f"顶会论文需要深度分析。"
                )

    # v5: 内容级质量检查（quality_engine）
    if tex:
        from quality_engine import (
            analyze_insight_density,
            analyze_motivation_guard,
            analyze_story_arc_depth,
            analyze_contribution_evidence,
        )

        issues = []
        issues += analyze_insight_density(tex)
        issues += analyze_motivation_guard(tex)
        issues += analyze_story_arc_depth(tex)
        skeleton = _load_json(project_dir, "artifacts/story_skeleton.json")
        if skeleton and isinstance(skeleton, dict):
            issues += analyze_contribution_evidence(tex, skeleton)

        for issue in issues:
            if issue.severity == "hard_fail":
                missing.append(f"\ud83d\udd34 {issue.message}")
            else:
                missing.append(f"\ud83d\udfe1 {issue.message}")

    return missing


def validate_review_round1(project_dir: str) -> list[str]:
    """review_round1: round1 审稿报告存在。"""
    missing = []
    data = _load_json(project_dir, "artifacts/review_round1.json")
    if data is None:
        missing.append("artifacts/review_round1.json 不存在或格式错误")
    return missing


def validate_revise_round1(project_dir: str) -> list[str]:
    """revise_round1: 修改后的 draft 存在。"""
    missing = []
    if not _file_exists(project_dir, "artifacts/draft_final.tex"):
        missing.append("artifacts/draft_final.tex 不存在")
    return missing


def validate_review_round2(project_dir: str) -> list[str]:
    """review_round2: round2 审稿报告存在。"""
    missing = []
    data = _load_json(project_dir, "artifacts/review_round2.json")
    if data is None:
        missing.append("artifacts/review_round2.json 不存在或格式错误")
    return missing


def validate_revise_round2(project_dir: str) -> list[str]:
    """revise_round2: 修改后的 draft 存在。"""
    missing = []
    if not _file_exists(project_dir, "artifacts/draft_final.tex"):
        missing.append("artifacts/draft_final.tex 不存在")
    return missing


def validate_review_round3_meta(project_dir: str) -> list[str]:
    """review_round3_meta: meta review 报告存在。"""
    missing = []
    data = _load_json(project_dir, "artifacts/meta_review.json")
    if data is None:
        missing.append("artifacts/meta_review.json 不存在或格式错误")
    return missing


def validate_final_revise(project_dir: str) -> list[str]:
    """final_revise: 终稿 + venue compliance + 引用一致性 + reproducibility checklist。"""
    missing = []
    if not _file_exists(project_dir, "artifacts/draft_final.tex"):
        missing.append("artifacts/draft_final.tex 不存在")

    # Reproducibility checklist
    if not _file_exists(project_dir, "artifacts/reproducibility_checklist.md"):
        missing.append("artifacts/reproducibility_checklist.md 不存在")

    # v3: Venue-aware pre-submission compliance
    tex = _read_text(project_dir, "artifacts/draft_final.tex")
    if tex:
        state = _load_json(project_dir, "project_state.json")
        venue = (state or {}).get("target_venue", "")
        playbook = _load_venue_playbook(venue) if venue else None

        if playbook:
            # 从 playbook 加载匿名化 patterns
            for pat in playbook.get("anonymization_patterns", []):
                if re.search(pat, tex, re.IGNORECASE):
                    missing.append(f"⚠️ 匿名化违规（{venue} playbook）: '{pat}'")

            # 必要章节检查
            for section in playbook.get("required_sections", []):
                if section.lower() not in tex.lower():
                    missing.append(f"⚠️ {venue} 要求 '{section}' section")

            # 页数检查
            max_pages = playbook.get("max_pages")
            if max_pages:
                estimated = _estimate_pages(tex)
                if estimated and estimated > max_pages:
                    missing.append(
                        f"⚠️ 预估 {estimated} 页，{venue} 限制 {max_pages} 页"
                    )

            # 必需实验类型检查
            for exp_type in playbook.get("mandatory_experiments", []):
                results = _load_json(project_dir, "artifacts/experiment_results.json")
                if results and isinstance(results, dict):
                    all_names = " ".join(
                        str(a.get("name", a)) for a in results.get("ablation_table", [])
                    ).lower()
                    if exp_type.lower() not in all_names:
                        missing.append(
                            f"⚠️ {venue} 要求 '{exp_type}' 实验但未找到"
                        )
        else:
            # 通用匿名化检查（无 playbook 时 fallback）
            anon_patterns = [
                r'\\author\{[^}]*[A-Z][a-z]+\s+[A-Z][a-z]+',  # 实名作者
            ]
            for pat in anon_patterns:
                if re.search(pat, tex):
                    missing.append(f"⚠️ 匿名化疑似违规（匹配: {pat[:30]}...）")

    # v2: 引用一致性
    if tex:
        bib_path = Path(project_dir) / "references.bib"
        if bib_path.exists():
            bib_text = bib_path.read_text(encoding="utf-8", errors="ignore")
            bib_keys = set(re.findall(r'@\w+\{(\w+)', bib_text))

            cite_keys = set()
            for group in re.findall(r'\\cite\{([^}]+)\}', tex):
                cite_keys.update(k.strip() for k in group.split(","))

            # 引用了但 bib 中没有
            for key in cite_keys:
                if key not in bib_keys:
                    missing.append(f"\\cite{{{key}}} 不在 references.bib 中")

            # bib 中有但未引用（警告，不 block）
            unused = bib_keys - cite_keys
            if len(unused) > 3:
                missing.append(
                    f"⚠️ references.bib 中有 {len(unused)} 条未引用的条目，建议清理"
                )

    return missing


# ---------- Validator 注册表 ---------- #

VALIDATORS: dict[str, callable] = {
    "insight_interview": validate_insight_interview,
    "survey_search": validate_survey_search,
    "survey_fetch": validate_survey_fetch,
    "evidence_audit": validate_evidence_audit,
    "domain_calibration": validate_domain_calibration,
    "ideation": validate_ideation,
    "deep_dive": validate_deep_dive,
    "novelty_check": validate_novelty_check,
    "experiment_design": validate_experiment_design,
    "pilot_experiment": validate_pilot_experiment,
    "experiment_run": validate_experiment_run,
    "venue_fit_check": validate_venue_fit_check,
    "writing": validate_writing,
    "review_round1": validate_review_round1,
    "revise_round1": validate_revise_round1,
    "review_round2": validate_review_round2,
    "revise_round2": validate_revise_round2,
    "review_round3_meta": validate_review_round3_meta,
    "final_revise": validate_final_revise,
}


def validate_stage(stage_name: str, project_dir: str) -> list[str]:
    """验证指定 stage 的产出是否完整。"""
    validator = VALIDATORS.get(stage_name)
    if validator is None:
        return [f"未知 stage: {stage_name}"]
    return validator(project_dir)
