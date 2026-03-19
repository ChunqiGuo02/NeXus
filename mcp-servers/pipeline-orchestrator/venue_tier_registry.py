"""会议/期刊分级注册表 — 领域可配置的 venue 质量分层。

Tier 1 = 顶会/顶刊 (NeurIPS, ICML, ICLR, CVPR, ICCV, ACL, ...)
Tier 2 = 强会 (AAAI, EMNLP, ECCV, ACM MM, IJCAI, ICRA, CoLT, ...)
Tier 3 = 普通会 (NAACL, COLING, BMVC, WACV, ...)

用户可通过 venue_tier_config.json 覆盖/扩展默认分级。
"""

from __future__ import annotations

import json
from pathlib import Path

# 按领域组织的默认 venue tier
DEFAULT_TIERS: dict[str, dict[str, list[str]]] = {
    "ai_ml": {
        "tier_1": ["NeurIPS", "ICML", "ICLR"],
        "tier_2": ["AAAI", "IJCAI", "AISTATS", "UAI", "CoLT"],
        "tier_3": ["ACML", "ECML-PKDD", "AutoML Conf"],
    },
    "cv": {
        "tier_1": ["CVPR", "ICCV"],
        "tier_2": ["ECCV", "ACM MM"],
        "tier_3": ["WACV", "BMVC", "ICIP", "ICPR"],
    },
    "nlp": {
        "tier_1": ["ACL"],
        "tier_2": ["EMNLP", "Findings of ACL/EMNLP"],
        "tier_3": ["NAACL", "COLING", "EACL", "AACL", "LREC"],
    },
    "robotics": {
        "tier_1": ["RSS", "CoRL"],
        "tier_2": ["ICRA", "IROS"],
        "tier_3": ["Humanoids", "ISER", "RoboSoft"],
    },
    "data_mining": {
        "tier_1": ["KDD", "WWW", "SIGIR", "WSDM"],
        "tier_2": ["CIKM", "ICDM", "SDM", "ECIR"],
        "tier_3": ["PAKDD", "DASFAA", "WISE"],
    },
    "journals": {
        "tier_1": ["TPAMI", "IJCV", "JMLR", "TACL", "Nature MI"],
        "tier_2": ["TIP", "TNNLS", "PR", "TMM", "TKDE"],
        "tier_3": ["Neurocomputing", "NCAA", "ESWA"],
    },
}


def get_tier_for_venue(
    venue_name: str,
    field: str = "auto",
    user_overrides: dict | None = None,
) -> int | None:
    """返回 venue 的 tier（1/2/3），未知 venue 返回 None。

    Parameters
    ----------
    venue_name : str
        会议/期刊名称。
    field : str
        领域名称，"auto" 表示自动检测。
    user_overrides : dict | None
        用户自定义的 tier 覆盖。

    Returns
    -------
    int | None
        1, 2, 3 或 None（未知 venue）。
    """
    tiers = _merge_tiers(user_overrides)
    venue_lower = venue_name.lower().strip()

    fields_to_search = (
        list(tiers.keys()) if field == "auto" else [field]
    )

    for f in fields_to_search:
        field_tiers = tiers.get(f, {})
        for tier_name, venues in field_tiers.items():
            for v in venues:
                if v.lower() == venue_lower:
                    return int(tier_name.split("_")[1])

    return None


def get_venues_for_field(
    field: str,
    user_overrides: dict | None = None,
) -> dict[str, list[str]]:
    """返回指定领域的全部 venue tier 映射。"""
    tiers = _merge_tiers(user_overrides)
    return tiers.get(field, {})


def get_all_tier1_venues(
    user_overrides: dict | None = None,
) -> list[str]:
    """返回所有领域的 Tier-1 venues。"""
    tiers = _merge_tiers(user_overrides)
    result: list[str] = []
    for field_tiers in tiers.values():
        result.extend(field_tiers.get("tier_1", []))
    return result


def detect_field(venue_name: str) -> str | None:
    """根据 venue 名称推断所属领域。"""
    venue_lower = venue_name.lower().strip()
    for field, field_tiers in DEFAULT_TIERS.items():
        for venues in field_tiers.values():
            for v in venues:
                if v.lower() == venue_lower:
                    return field
    return None


def load_user_overrides(project_dir: str) -> dict | None:
    """加载用户自定义的 venue tier 覆盖配置。

    从 {project_dir}/venue_tier_config.json 读取。
    """
    config_path = Path(project_dir) / "venue_tier_config.json"
    if not config_path.exists():
        config_path = Path(project_dir) / "artifacts/venue_tier_config.json"
    if not config_path.exists():
        return None

    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def determine_time_range(
    topic_paper_count_per_year: int,
) -> int:
    """根据方向年发文量确定爬取时间范围（年数）。

    核心逻辑: 热门方向样本多→短时间就够，冷门方向样本少→需要更长。

    Parameters
    ----------
    topic_paper_count_per_year : int
        目标 venue 近 1 年该 topic 的论文数量。

    Returns
    -------
    int
        建议的时间范围（年数）。
    """
    if topic_paper_count_per_year > 20:
        return 3  # 热门: 3 年
    elif topic_paper_count_per_year >= 5:
        return 4  # 中等: 4 年
    else:
        return 6  # 冷门: 最多 6 年


def _merge_tiers(user_overrides: dict | None) -> dict:
    """合并默认 tiers 和用户覆盖。"""
    import copy

    result = copy.deepcopy(DEFAULT_TIERS)
    if not user_overrides:
        return result

    for field, field_tiers in user_overrides.items():
        if field not in result:
            result[field] = {}
        for tier_name, venues in field_tiers.items():
            if tier_name in result[field]:
                # 追加去重
                existing = {v.lower() for v in result[field][tier_name]}
                for v in venues:
                    if v.lower() not in existing:
                        result[field][tier_name].append(v)
            else:
                result[field][tier_name] = venues

    return result
