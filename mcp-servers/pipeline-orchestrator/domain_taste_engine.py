"""自动领域品味学习引擎 — 通过分析不同 tier 的论文来学习领域标准。

三层分析:
1. 结构分析（全量，零 LLM 成本，纯正则/NLP）
2. LLM 精读（跨全 tier，每 tier 5-8 篇）
3. 纵向趋势分析（时间维度）

输出 domain_taste_profile.json + exemplar_structures.json。
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass


@dataclass
class PaperStructure:
    """单篇论文的结构分析结果。"""

    paper_id: str
    tier: str  # "tier1_elite" / "tier1_poster" / "tier2" / "tier3"
    venue: str = ""

    # 结构维度
    total_words: int = 0
    num_sections: int = 0
    num_figures: int = 0
    num_tables: int = 0
    num_equations: int = 0
    insight_density: float = 0.0
    intro_paragraphs: int = 0
    intro_words: int = 0
    method_words: int = 0
    experiment_words: int = 0
    related_work_words: int = 0

    # 实验深度
    has_ablation: bool = False
    has_case_study: bool = False
    has_failure_analysis: bool = False
    has_efficiency_analysis: bool = False
    has_sensitivity_analysis: bool = False

    # 公式前 motivation
    formulas_with_motivation: int = 0
    formulas_total: int = 0

    # 参考文献
    num_references: int = 0


def parse_paper_structure(
    markdown: str,
    paper_id: str,
    tier: str,
    venue: str = "",
) -> PaperStructure:
    """对单篇论文做结构分析。全部用正则/NLP，零 LLM 成本。

    Parameters
    ----------
    markdown : str
        论文的 Markdown 全文。
    paper_id : str
        论文 ID。
    tier : str
        论文所属 tier，如 "tier1_elite"。
    venue : str
        发表 venue 名称。

    Returns
    -------
    PaperStructure
        结构分析结果。
    """
    ps = PaperStructure(paper_id=paper_id, tier=tier, venue=venue)

    # 基础统计
    words = markdown.split()
    ps.total_words = len(words)
    ps.num_sections = len(re.findall(r"^##?\s", markdown, re.MULTILINE))
    ps.num_figures = len(
        re.findall(r"(?:figure|fig\.?\s*\d|!\[)", markdown, re.IGNORECASE)
    )
    ps.num_tables = len(
        re.findall(r"(?:table\s+\d|\|.*\|.*\|)", markdown, re.IGNORECASE)
    )
    ps.num_equations = len(
        re.findall(r"\$\$.*?\$\$|\\\[.*?\\\]", markdown, re.DOTALL)
    )
    ps.num_references = len(
        re.findall(r"\[\d+\]|\\\cite\{", markdown)
    )

    # Section 级分析
    sections = _split_sections(markdown)

    intro = sections.get("introduction", "")
    ps.intro_paragraphs = len(
        [p for p in intro.split("\n\n") if p.strip()]
    )
    ps.intro_words = len(intro.split())

    method = sections.get("method", "")
    ps.method_words = len(method.split())

    experiment = sections.get("experiment", "")
    ps.experiment_words = len(experiment.split())

    related = sections.get("related_work", "")
    ps.related_work_words = len(related.split())

    # 实验深度
    exp_lower = experiment.lower()
    ps.has_ablation = bool(
        re.search(r"ablation|component\s+analysis|w/o\s+\w+", exp_lower)
    )
    ps.has_case_study = bool(
        re.search(r"case\s+stud|qualitative|visualization", exp_lower)
    )
    ps.has_failure_analysis = bool(
        re.search(r"failur|limitation|when\s+(?:it\s+)?fails", exp_lower)
    )
    ps.has_efficiency_analysis = bool(
        re.search(r"efficien|speed|runtime|fps|latency", exp_lower)
    )
    ps.has_sensitivity_analysis = bool(
        re.search(r"sensitiv|robustness|hyperparameter", exp_lower)
    )

    # Insight density
    paragraphs = [p for p in markdown.split("\n\n") if p.strip()]
    if paragraphs:
        from quality_engine import _has_insight_marker

        with_marker = sum(1 for p in paragraphs if _has_insight_marker(p))
        ps.insight_density = round(with_marker / len(paragraphs), 3)

    # 公式 motivation 检测
    formula_pattern = r"\$\$.*?\$\$|\\\[.*?\\\]"
    formulas = list(re.finditer(formula_pattern, markdown, re.DOTALL))
    ps.formulas_total = len(formulas)
    from quality_engine import MOTIVATION_KEYWORDS

    for m in formulas:
        start = max(0, m.start() - 500)
        context = markdown[start : m.start()]
        if re.search(MOTIVATION_KEYWORDS, context, re.IGNORECASE):
            ps.formulas_with_motivation += 1

    return ps


def compute_differential(
    tier1_elite: list[PaperStructure],
    tier1_poster: list[PaperStructure],
    tier2: list[PaperStructure],
    tier3: list[PaperStructure],
) -> dict:
    """计算四层阶梯差异：Elite vs Poster, Poster vs Tier2, Tier2 vs Tier3。

    返回阶梯差异报告，精确定位每一层之间的质量差距。
    """
    groups = {
        "tier1_elite": tier1_elite,
        "tier1_poster": tier1_poster,
        "tier2": tier2,
        "tier3": tier3,
    }
    diff: dict = {}

    dimensions: list[tuple[str, object]] = [
        ("total_words", lambda ps: ps.total_words),
        ("num_figures", lambda ps: ps.num_figures),
        ("num_tables", lambda ps: ps.num_tables),
        ("num_equations", lambda ps: ps.num_equations),
        ("insight_density", lambda ps: ps.insight_density),
        ("intro_paragraphs", lambda ps: ps.intro_paragraphs),
        ("intro_words", lambda ps: ps.intro_words),
        ("has_ablation", lambda ps: int(ps.has_ablation)),
        ("has_case_study", lambda ps: int(ps.has_case_study)),
        ("has_failure_analysis", lambda ps: int(ps.has_failure_analysis)),
        ("has_efficiency_analysis", lambda ps: int(ps.has_efficiency_analysis)),
        ("formulas_with_motivation_ratio", lambda ps: (
            ps.formulas_with_motivation / max(ps.formulas_total, 1)
        )),
        ("num_references", lambda ps: ps.num_references),
    ]

    for name, extractor in dimensions:
        group_means: dict[str, float] = {}
        for gname, papers in groups.items():
            vals = [extractor(p) for p in papers]
            group_means[gname] = (
                round(statistics.mean(vals), 2) if vals else 0
            )
        diff[name] = {
            **group_means,
            # 阶梯差异比率
            "elite_vs_poster": round(
                group_means["tier1_elite"]
                / max(group_means["tier1_poster"], 0.01),
                2,
            ),
            "tier1_vs_tier2": round(
                group_means["tier1_poster"]
                / max(group_means["tier2"], 0.01),
                2,
            ),
            "tier2_vs_tier3": round(
                group_means["tier2"]
                / max(group_means["tier3"], 0.01),
                2,
            ),
        }

    # Section 级别对比
    for section in ("intro_words", "method_words", "experiment_words"):
        def extractor(ps, s=section):
            return getattr(ps, s, 0)
        group_means = {}
        for gname, papers in groups.items():
            vals = [extractor(p) for p in papers]
            group_means[gname] = (
                round(statistics.mean(vals), 2) if vals else 0
            )
        diff[f"section_{section}"] = group_means

    return diff


def generate_taste_profile(
    diff: dict,
    sample_sizes: dict[str, int],
    venue: str,
    topic_area: str,
    time_range: tuple[int, int],
) -> dict:
    """基于差异分析生成 domain_taste_profile.json。

    Parameters
    ----------
    diff : dict
        compute_differential() 的输出。
    sample_sizes : dict
        各组的样本量。
    venue : str
        目标 venue。
    topic_area : str
        研究方向。
    time_range : tuple[int, int]
        数据的时间范围 (start_year, end_year)。

    Returns
    -------
    dict
        完整的 domain taste profile。
    """
    profile: dict = {
        "venue": venue,
        "topic_area": topic_area,
        "time_range": {"start": time_range[0], "end": time_range[1]},
        "sample_sizes": sample_sizes,
        "structural_norms": diff,
    }

    # 生成 acceptance_bar (达到 tier1 poster 的最低标准)
    profile["acceptance_bar"] = _derive_bar(diff, "tier1_poster")

    # 生成 excellence_bar (达到 oral/spotlight 的标准)
    profile["excellence_bar"] = _derive_bar(diff, "tier1_elite")

    # 生成 concrete_writing_rules
    profile["concrete_writing_rules"] = _derive_rules(diff)

    # 生成 must_have_baselines (需要 LLM 辅助，这里只是占位)
    profile["must_have_baselines"] = []

    # trending_direction (需要纵向分析，占位)
    profile["trending_direction"] = ""

    return profile


def _derive_bar(diff: dict, tier_key: str) -> dict:
    """从差异数据中提取指定 tier 的标准。"""
    bar: dict = {}
    for dim, values in diff.items():
        if isinstance(values, dict) and tier_key in values:
            bar[dim] = values[tier_key]
    return bar


def _derive_rules(diff: dict) -> list[str]:
    """从差异中提炼写作硬规则。"""
    rules: list[str] = []

    # Insight density
    elite_density = diff.get("insight_density", {}).get("tier1_elite", 0)
    if elite_density > 0:
        threshold = round(elite_density * 0.7, 2)
        rules.append(f"Insight density 必须 ≥ {threshold}")

    # Ablation
    elite_ablation = diff.get("has_ablation", {}).get("tier1_elite", 0)
    if elite_ablation >= 0.9:
        rules.append("Experiment 必须包含 ablation study")

    # Intro
    elite_intro = diff.get("intro_paragraphs", {}).get("tier1_elite", 0)
    if elite_intro > 0:
        min_paras = max(int(elite_intro * 0.8), 3)
        rules.append(f"Introduction 至少 {min_paras} 段")

    # Figures
    elite_figs = diff.get("num_figures", {}).get("tier1_elite", 0)
    if elite_figs > 0:
        min_figs = max(int(elite_figs * 0.7), 4)
        rules.append(f"图表数 ≥ {min_figs}")

    # Failure analysis
    elite_failure = diff.get("has_failure_analysis", {}).get(
        "tier1_elite", 0
    )
    if elite_failure >= 0.5:
        rules.append("强烈建议包含 failure analysis")

    # Motivation
    elite_motivation = diff.get(
        "formulas_with_motivation_ratio", {}
    ).get("tier1_elite", 0)
    if elite_motivation >= 0.8:
        rules.append("每个公式/算法前必须有动机解释")

    return rules


def _split_sections(markdown: str) -> dict[str, str]:
    """将 markdown 按 section 拆分。"""
    sections: dict[str, str] = {}
    current = "preamble"
    current_content: list[str] = []

    for line in markdown.split("\n"):
        header_match = re.match(r"^##?\s+(.+)", line)
        if header_match:
            if current_content:
                sections[current] = "\n".join(current_content)
            title = header_match.group(1).strip()
            current = _classify_section_name(title)
            current_content = []
        else:
            current_content.append(line)

    if current_content:
        sections[current] = "\n".join(current_content)

    return sections


def _classify_section_name(title: str) -> str:
    """将 section 标题归类为标准名称。"""
    t = title.lower()
    if "intro" in t:
        return "introduction"
    if any(kw in t for kw in ("method", "approach", "model", "framework")):
        return "method"
    if any(kw in t for kw in ("experiment", "result", "evaluation")):
        return "experiment"
    if "related" in t:
        return "related_work"
    if "conclu" in t:
        return "conclusion"
    if "abstract" in t:
        return "abstract"
    return t.replace(" ", "_")[:30]
