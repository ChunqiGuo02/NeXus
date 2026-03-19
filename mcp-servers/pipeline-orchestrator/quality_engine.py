"""论文内容质量分析引擎 — 用 NLP 检查替代 LLM 自省。

4 个独立分析器，每个返回 list[QualityIssue]。
validators.py 在 validate_writing() 中调用。

阈值可从 domain_taste_profile.json 动态加载。
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class QualityIssue:
    """单条质量问题。"""

    analyzer: str
    severity: str  # "hard_fail" / "soft_warn"
    message: str
    location: str = ""  # 行号或段落位置


# ── Insight Markers ──

INSIGHT_MARKERS: dict[str, str] = {
    "quantitative": r"\d+\.?\d*\s*%|improves?\s+by|reduces?\s+by|achieves?\s+\d",
    "causal": r"\bbecause\b|\bdue to\b|\bcaused by\b|\bleads to\b|\bresults? in\b",
    "contrast": r"\bunlike\b|\bin contrast\b|\bcompared to\b|\bwhereas\b",
    "surprising": (
        r"\bsurprising(?:ly)?\b|\bcounter-?intuitiv"
        r"|unexpect(?:ed)?ly|\binteresting(?:ly)?\b"
    ),
    "connection": r"\bconnect(?:s|ing)?\s+to\b|\banalogous\b|\breminiscent\b",
}

MOTIVATION_KEYWORDS = (
    r"\bto address\b|\bmotivated by\b|\bto handle\b|\bthis enables?\b|"
    r"\bto avoid\b|\bto capture\b|\bto model\b|\bto overcome\b|"
    r"\bin order to\b|\ballows? us\b|\bthe key (?:idea|insight)\b|"
    r"\bto inject\b|\bto mitigate\b|\bto enforce\b"
)


# ── 分析器 1: Insight Density Analyzer ──


def analyze_insight_density(
    tex: str,
    *,
    desert_threshold_intro: int = 2,
    desert_threshold_method: int = 2,
    desert_threshold_experiment: int = 3,
) -> list[QualityIssue]:
    """检测 insight 沙漠——连续多段无实质内容。

    Parameters
    ----------
    tex : str
        论文 tex 全文。
    desert_threshold_intro : int
        Introduction 中连续无 marker 段落的阈值。
    desert_threshold_method : int
        Method 中连续无 marker 段落的阈值。
    desert_threshold_experiment : int
        Experiment 中连续无 marker 段落的阈值。

    Returns
    -------
    list[QualityIssue]
        发现的质量问题列表。
    """
    issues: list[QualityIssue] = []
    paragraphs = _split_paragraphs(tex)

    # 按 section 分组
    current_section = "unknown"
    section_paras: dict[str, list[str]] = {}

    for para in paragraphs:
        section_match = re.search(
            r"\\(?:section|subsection)\{([^}]+)\}", para
        )
        if section_match:
            current_section = _classify_section(section_match.group(1))
        section_paras.setdefault(current_section, []).append(para)

    thresholds = {
        "introduction": desert_threshold_intro,
        "method": desert_threshold_method,
        "experiment": desert_threshold_experiment,
    }

    for section, paras in section_paras.items():
        if section not in thresholds:
            continue  # 跳过非主要 section (related_work, conclusion, other)
        threshold = thresholds[section]
        consecutive_empty = 0
        for i, para in enumerate(paras):
            if _has_insight_marker(para):
                consecutive_empty = 0
            else:
                consecutive_empty += 1
                if consecutive_empty >= threshold:
                    severity = (
                        "hard_fail"
                        if section in ("introduction", "method")
                        else "soft_warn"
                    )
                    issues.append(
                        QualityIssue(
                            analyzer="insight_density",
                            severity=severity,
                            message=(
                                f"Insight Desert: {section} 中连续"
                                f" {consecutive_empty} 段无实质内容"
                                f"（段 {i - consecutive_empty + 2}-{i + 1}）"
                            ),
                            location=f"{section}:para_{i + 1}",
                        )
                    )

    # 全文 insight density
    total = len(paragraphs)
    if total > 0:
        with_marker = sum(1 for p in paragraphs if _has_insight_marker(p))
        density = with_marker / total
        if density < 0.3:
            issues.append(
                QualityIssue(
                    analyzer="insight_density",
                    severity="hard_fail",
                    message=(
                        f"全文 insight density = {density:.2f} (需 ≥ 0.3)。"
                        f" {total - with_marker}/{total} 段缺少实质内容"
                    ),
                )
            )

    return issues


# ── 分析器 2: Motivation Guard ──


def analyze_motivation_guard(tex: str) -> list[QualityIssue]:
    """检测公式/算法前是否有"为什么需要这个"的解释。"""
    issues: list[QualityIssue] = []

    # 查找公式环境
    equation_patterns = [
        r"\\begin\{equation\}",
        r"\\begin\{align\}",
        r"\\begin\{aligned\}",
        r"\$\$",
    ]
    combined = "|".join(equation_patterns)

    lines = tex.split("\n")
    for i, line in enumerate(lines):
        if re.search(combined, line):
            # 向前看 5 行，检查是否有 motivation
            context = "\n".join(lines[max(0, i - 5) : i])
            if not re.search(MOTIVATION_KEYWORDS, context, re.IGNORECASE):
                issues.append(
                    QualityIssue(
                        analyzer="motivation_guard",
                        severity="hard_fail",
                        message=(
                            f"公式缺少 motivation: line {i + 1} 的公式前"
                            " 5 行未找到动机解释"
                        ),
                        location=f"line_{i + 1}",
                    )
                )

    return issues


# ── 分析器 3: Experiment Story Arc Enforcer ──


def analyze_story_arc_depth(tex: str) -> list[QualityIssue]:
    """检查实验是否有完整的 story arc。"""
    issues: list[QualityIssue] = []

    required_sections = {
        "setup": r"(?:experimental?\s+)?setup|implementation\s+details?",
        "main_results": r"main\s+results?|comparison|quantitative",
        "ablation": r"ablation|component\s+analysis",
        "analysis": r"case\s+stud|qualitative|visualization|analysis",
        "limitation": r"limitation|failure|when\s+(?:it\s+)?fails?",
    }
    optional_sections = {
        "efficiency": r"efficien|speed|runtime|complexity|cost",
        "sensitivity": r"sensitiv|robustness|hyperparameter",
    }

    tex_lower = tex.lower()

    for name, pattern in required_sections.items():
        if not re.search(pattern, tex_lower):
            issues.append(
                QualityIssue(
                    analyzer="story_arc",
                    severity="hard_fail",
                    message=f"实验缺少 {name} 部分",
                    location="experiment_section",
                )
            )

    for name, pattern in optional_sections.items():
        if not re.search(pattern, tex_lower):
            issues.append(
                QualityIssue(
                    analyzer="story_arc",
                    severity="soft_warn",
                    message=f"实验缺少 {name} 部分（推荐但非必须）",
                    location="experiment_section",
                )
            )

    return issues


# ── 分析器 4: Contribution-Evidence Cross-Validator ──


def analyze_contribution_evidence(
    tex: str, skeleton: dict
) -> list[QualityIssue]:
    """检查每个 contribution 是否有实验支撑。"""
    issues: list[QualityIssue] = []

    contributions: list[str] = skeleton.get("contributions", [])
    if not contributions:
        issues.append(
            QualityIssue(
                analyzer="contribution_evidence",
                severity="hard_fail",
                message="story_skeleton.json 中无 contributions 列表",
            )
        )
        return issues

    # 提取 table/figure captions
    captions = re.findall(
        r"\\caption\{([^}]+)\}", tex, re.IGNORECASE
    )
    caption_text = " ".join(captions).lower()

    for i, contrib in enumerate(contributions):
        # 提取 contribution 的关键词（取前 5 个非 stop word）
        keywords = _extract_keywords(contrib)
        matched = any(kw in caption_text for kw in keywords)

        if not matched:
            issues.append(
                QualityIssue(
                    analyzer="contribution_evidence",
                    severity="hard_fail",
                    message=(
                        f"Contribution {i + 1} 缺少实验支撑: "
                        f"'{contrib[:60]}...' 未匹配到相关 table/figure"
                    ),
                    location=f"contribution_{i + 1}",
                )
            )

    return issues


# ── 辅助函数 ──

_STOP_WORDS = frozenset(
    "a an the we our this that is are was were be been has have had "
    "do does did will would shall should may might can could of in on "
    "at to for with by from and or but not".split()
)


def _split_paragraphs(tex: str, min_length: int = 50) -> list[str]:
    """将 tex 按空行分段，过滤空段、纯命令行和过短段落。"""
    raw = re.split(r"\n\s*\n", tex)
    return [
        p.strip()
        for p in raw
        if p.strip()
        and not p.strip().startswith("%")
        and len(p.strip()) >= min_length
    ]


def _has_insight_marker(para: str) -> bool:
    """检查段落是否包含至少 1 个 insight marker。"""
    for pattern in INSIGHT_MARKERS.values():
        if re.search(pattern, para, re.IGNORECASE):
            return True
    return False


def _classify_section(title: str) -> str:
    """将 section 标题归类。"""
    t = title.lower()
    if "intro" in t:
        return "introduction"
    if "method" in t or "approach" in t or "model" in t or "framework" in t:
        return "method"
    if "experiment" in t or "result" in t or "evaluation" in t:
        return "experiment"
    if "related" in t:
        return "related_work"
    if "conclu" in t:
        return "conclusion"
    return "other"


def _extract_keywords(text: str, max_kw: int = 5) -> list[str]:
    """提取文本的关键词。"""
    words = re.findall(r"[a-z]+", text.lower())
    return [w for w in words if w not in _STOP_WORDS][:max_kw]
