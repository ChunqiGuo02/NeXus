"""SDP 交接文件生成器 — 为跨模型/跨插件任务生成自包含指令。

核心原则: GPT 不读 SKILL.md/MCP，所有上下文必须嵌入 handoff。
调用时机: Antigravity 在每次 SDP 交接前调用。
输出: dialogue/sdp_handoff.json（~5000-8000 字的自包含指令）
"""

from __future__ import annotations

import json
from pathlib import Path


def generate_handoff(
    task_type: str,
    project_dir: str,
    reviewer_count: int = 3,
) -> dict:
    """生成自包含的 SDP handoff 文件。

    Parameters
    ----------
    task_type : str
        任务类型: "review" / "red_team" / "arch_review" / "polish"
    project_dir : str
        项目目录。
    reviewer_count : int
        审稿人数量（仅 review 类型使用）。

    Returns
    -------
    dict
        完整的 handoff 数据，写到 dialogue/sdp_handoff.json。
    """
    taste = _load_json(project_dir, "artifacts/domain_taste_profile.json")
    state = _load_json(project_dir, "project_state.json")

    if task_type == "review":
        handoff = _generate_review_handoff(
            taste, state, project_dir, reviewer_count
        )
    elif task_type == "red_team":
        handoff = _generate_red_team_handoff(taste, state, project_dir)
    elif task_type == "arch_review":
        handoff = _generate_arch_review_handoff(
            taste, state, project_dir
        )
    elif task_type == "polish":
        handoff = _generate_polish_handoff(taste, state, project_dir)
    else:
        handoff = {"error": f"Unknown task_type: {task_type}"}

    # 写到文件
    output_path = Path(project_dir) / "dialogue" / "sdp_handoff.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(handoff, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return handoff


def _generate_review_handoff(
    taste: dict | None,
    state: dict | None,
    project_dir: str,
    n_reviewers: int,
) -> dict:
    """生成审稿任务的 handoff。"""
    venue = (state or {}).get("target_venue", "Unknown")
    topic = (state or {}).get("topic_area", "Unknown")

    # 构建 domain context briefing
    domain_briefing = _build_domain_briefing(taste)

    # 构建 reviewer personas
    personas = _build_reviewer_personas(
        taste, n_reviewers, venue
    )

    return {
        "task": "review",
        "model": "gpt-5.4",
        "venue": venue,
        "topic": topic,
        "domain_context": domain_briefing,
        "reviewers": personas,
        "scoring_rules": {
            "scale": "1-10, 6='marginally above', 5='marginally below'",
            "constraints": [
                "至少 1 个 reviewer score ≤ 5",
                "至少 2 个 reviewer score ≤ 6",
                "每个 reviewer 必须给出 reject_level_weakness",
            ],
        },
        "review_template": (
            "按以下结构输出审稿意见:\n"
            "1. Summary (2-3句)\n"
            "2. Strengths (≥3条，具体到段落/公式/图表)\n"
            "3. Weaknesses (≥3条，每条必须指出具体位置)\n"
            "4. Questions (≥2条)\n"
            "5. Missing References\n"
            "6. reject_level_weakness (至少1条)\n"
            "7. Overall Score (1-10)\n"
            "8. Confidence (1-5)"
        ),
        "input_files": [
            "artifacts/draft_final.tex",
            "artifacts/experiment_results.json",
        ],
        "output_files": [
            f"dialogue/review_gpt_{i}.json"
            for i in range(n_reviewers)
        ],
    }


def _generate_red_team_handoff(
    taste: dict | None,
    state: dict | None,
    project_dir: str,
) -> dict:
    """生成红队攻击任务的 handoff。"""
    return {
        "task": "red_team",
        "model": "gpt-5.4",
        "domain_context": _build_domain_briefing(taste),
        "attack_dimensions": [
            "技术可行性",
            "实验可验证性",
            "与 prior art 的差异度",
            "contribution magnitude",
            "venue fit",
        ],
        "instructions": (
            "你是一个学术红队攻击者。\n"
            "阅读以下 idea，从 5 个维度尽可能找出弱点。\n"
            "每个维度至少提出 1 个具体攻击点。\n"
            "攻击必须具体、可操作，不能是泛泛而谈。"
        ),
        "input_files": ["dialogue/ideas_v1.md"],
        "output_files": ["dialogue/red_team_report.md"],
    }


def _generate_arch_review_handoff(
    taste: dict | None,
    state: dict | None,
    project_dir: str,
) -> dict:
    """生成架构审查任务的 handoff。"""
    return {
        "task": "arch_review",
        "model": "gpt-5.4",
        "domain_context": _build_domain_briefing(taste),
        "review_focus": [
            "数据流是否清晰合理",
            "模块职责是否单一",
            "是否有明显的设计缺陷",
            "可扩展性和可维护性",
        ],
        "input_files": ["experimental_design.md"],
        "output_files": ["dialogue/arch_review.md"],
    }


def _generate_polish_handoff(
    taste: dict | None,
    state: dict | None,
    project_dir: str,
) -> dict:
    """生成论文润色任务的 handoff。"""
    return {
        "task": "polish",
        "model": "gpt-5.4",
        "domain_context": _build_domain_briefing(taste),
        "polish_rules": [
            "去除 AI 典型表达",
            "增强段落间过渡",
            "强化 motivation 语句",
            "确保 claim 有定量支撑",
        ],
        "input_files": ["artifacts/draft_final.tex"],
        "output_files": ["artifacts/draft_polished.tex"],
    }


def _build_domain_briefing(taste: dict | None) -> str:
    """从 domain_taste_profile 构建详细的领域知识简报。

    这是 handoff 最重要的部分——GPT 不读 SKILL.md，
    所有领域知识必须在这里完整传达。
    """
    if not taste:
        return "（domain_taste_profile 不可用）"

    parts: list[str] = []

    # Venue 和 topic
    venue = taste.get("venue", "Unknown")
    topic = taste.get("topic_area", "Unknown")
    parts.append(
        f"目标 venue: {venue}, 研究方向: {topic}"
    )

    # 时间范围和样本量
    tr = taste.get("time_range", {})
    ss = taste.get("sample_sizes", {})
    parts.append(
        f"数据来源: {tr.get('start', '?')}-{tr.get('end', '?')},"
        f" 样本: elite={ss.get('tier1_elite', '?')},"
        f" poster={ss.get('tier1_poster', '?')},"
        f" tier2={ss.get('tier2', '?')},"
        f" tier3={ss.get('tier3', '?')}"
    )

    # 结构差异统计
    norms = taste.get("structural_norms", {})
    if norms:
        parts.append("\n【结构差异统计】")
        for dim, values in norms.items():
            if isinstance(values, dict):
                elite = values.get("tier1_elite", "?")
                poster = values.get("tier1_poster", "?")
                t2 = values.get("tier2", "?")
                t3 = values.get("tier3", "?")
                parts.append(
                    f"  {dim}: elite={elite}, poster={poster},"
                    f" tier2={t2}, tier3={t3}"
                )

    # 写作规则
    rules = taste.get("concrete_writing_rules", [])
    if rules:
        parts.append("\n【写作硬规则】")
        for r in rules:
            parts.append(f"  - {r}")

    # 必备 baseline
    baselines = taste.get("must_have_baselines", [])
    if baselines:
        parts.append(
            f"\n【必备 baseline】: {', '.join(baselines)}"
        )

    # Trending
    trending = taste.get("trending_direction", "")
    if trending:
        parts.append(f"\n【趋势方向】: {trending}")

    # Acceptance / Excellence bar
    acc_bar = taste.get("acceptance_bar", {})
    exc_bar = taste.get("excellence_bar", {})
    if acc_bar:
        parts.append(
            f"\n【Poster 最低标准】: {json.dumps(acc_bar, ensure_ascii=False)[:200]}"
        )
    if exc_bar:
        parts.append(
            f"【Oral 标准】: {json.dumps(exc_bar, ensure_ascii=False)[:200]}"
        )

    return "\n".join(parts)


def _build_reviewer_personas(
    taste: dict | None,
    n_reviewers: int,
    venue: str,
) -> list[dict]:
    """根据 domain taste 生成 reviewer personas。"""
    # 基础角色模板
    base_roles = [
        {
            "focus": "方法论",
            "style": "注重理论深度和方法设计的合理性",
        },
        {
            "focus": "实验",
            "style": "注重实验设计、baseline 完整性和统计严谨性",
        },
        {
            "focus": "对抗型",
            "style": "专门找弱点，倾向严格评审",
        },
        {
            "focus": "应用",
            "style": "注重实际影响力和可部署性",
        },
        {
            "focus": "写作",
            "style": "注重论文叙事、清晰度和说服力",
        },
        {
            "focus": "领域专家",
            "style": "深度关注该子领域的技术细节",
        },
    ]

    personas: list[dict] = []
    must_check_global: list[str] = []

    # 从 domain taste 生成 must_check
    if taste:
        norms = taste.get("structural_norms", {})
        baselines = taste.get("must_have_baselines", [])

        if baselines:
            must_check_global.append(
                f"是否与必备 baseline 对比: {', '.join(baselines)}"
            )

        ablation_pct = norms.get("has_ablation", {}).get(
            "tier1_elite", 0
        )
        if ablation_pct >= 0.9:
            must_check_global.append(
                f"ablation study (elite 论文 {ablation_pct*100:.0f}% 包含)"
            )

        failure_pct = norms.get("has_failure_analysis", {}).get(
            "tier1_elite", 0
        )
        if failure_pct >= 0.5:
            must_check_global.append(
                f"failure analysis (elite 论文 {failure_pct*100:.0f}% 包含)"
            )

    for i in range(n_reviewers):
        role = base_roles[i % len(base_roles)]
        persona = {
            "id": f"R-GPT-{chr(65 + i)}",
            "persona": {
                "role": (
                    f"你是一位在 {venue} 有多年审稿经验的"
                    f" {role['focus']} 专家"
                ),
                "focus": role["focus"],
                "style": role["style"],
            },
            "must_check": must_check_global.copy(),
        }
        personas.append(persona)

    return personas


def _load_json(project_dir: str, relative_path: str) -> dict | None:
    """加载 JSON 文件。"""
    path = Path(project_dir) / relative_path
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
