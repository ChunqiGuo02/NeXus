"""verify_citation MCP Tool

多源交叉核验引用真实性 + 撤稿检查。
至少两个独立数据源确认才标记为 VERIFIED。
支持无 DOI 时通过 title/authors/year 后备校验。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from sources import crossref, openalex, semantic_scholar
from shared import cache_get, cache_set, cache_key

logger = logging.getLogger("paper-service")

GLOBAL_CONFIG_PATH = Path.home() / ".aria" / "global_config.json"


def _load_config() -> dict:
    if GLOBAL_CONFIG_PATH.exists():
        return json.loads(GLOBAL_CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def register(mcp_instance: FastMCP) -> None:
    @mcp_instance.tool()
    async def verify_citation(
        doi: str | None = None,
        title: str | None = None,
        authors: list[str] | None = None,
        year: int | None = None,
    ) -> dict[str, Any]:
        """多源交叉核验引用 + 撤稿检查。

        Args:
            doi: DOI 标识符
            title: 论文标题（DOI 不可用时的备选）
            authors: 作者列表
            year: 出版年份

        Returns:
            {
                "status": "verified" | "unverified" | "retracted",
                "confidence": float (0-1),
                "sources_checked": list[str],
                "sources_confirmed": list[str],
                "is_retracted": bool,
                "retraction_source": str | None,
                "verified_metadata": dict,
                "discrepancies": list[str],
            }
        """
        config = _load_config()
        email = config.get("email")
        s2_key = config.get("semantic_scholar_key")

        sources_checked: list[str] = []
        sources_confirmed: list[str] = []
        verified_metadata: dict = {}
        discrepancies: list[str] = []
        is_retracted = False
        retraction_source = None

        # ── 路径 A: DOI 校验 ──
        if doi:
            # CrossRef
            try:
                ck = cache_key("crossref", doi)
                cr_data = cache_get(ck)
                if cr_data is None:
                    cr_data = await crossref.get_by_doi(doi, email=email)
                    if cr_data:
                        cache_set(ck, cr_data)
                sources_checked.append("crossref")
                if cr_data:
                    sources_confirmed.append("crossref")
                    verified_metadata["crossref"] = {
                        "title": cr_data.get("title"),
                        "authors": cr_data.get("authors"),
                        "year": cr_data.get("year"),
                        "venue": cr_data.get("venue"),
                    }
            except Exception as e:
                sources_checked.append("crossref")
                logger.warning(f"CrossRef 核验失败: {e}")

            # OpenAlex
            try:
                ck = cache_key("openalex", doi)
                oa_data = cache_get(ck)
                if oa_data is None:
                    oa_data = await openalex.get_by_doi(doi, email=email)
                    if oa_data:
                        cache_set(ck, oa_data)
                sources_checked.append("openalex")
                if oa_data:
                    sources_confirmed.append("openalex")
                    verified_metadata["openalex"] = {
                        "title": oa_data.get("title"),
                        "authors": oa_data.get("authors"),
                        "year": oa_data.get("year"),
                        "venue": oa_data.get("venue"),
                        "cited_by_count": oa_data.get("cited_by_count"),
                        "cited_by_percentile": oa_data.get("cited_by_percentile"),
                    }
                    if oa_data.get("is_retracted"):
                        is_retracted = True
                        retraction_source = "openalex"
            except Exception as e:
                sources_checked.append("openalex")
                logger.warning(f"OpenAlex 核验失败: {e}")

            # Semantic Scholar
            try:
                s2_data = await semantic_scholar.get_paper(f"DOI:{doi}", api_key=s2_key)
                sources_checked.append("semantic_scholar")
                if s2_data:
                    sources_confirmed.append("semantic_scholar")
                    s2_authors = s2_data.get("authors", [])
                    if isinstance(s2_authors, list) and s2_authors:
                        if isinstance(s2_authors[0], dict):
                            s2_authors = [a.get("name", "") for a in s2_authors]
                    verified_metadata["semantic_scholar"] = {
                        "title": s2_data.get("title"),
                        "authors": s2_authors,
                        "year": s2_data.get("year"),
                        "venue": s2_data.get("venue"),
                        "citation_count": s2_data.get("citationCount"),
                    }
            except Exception as e:
                sources_checked.append("semantic_scholar")
                logger.warning(f"Semantic Scholar 核验失败: {e}")

        # ── 路径 B: 无 DOI 时用 title+authors+year 后备校验 ──
        elif title:
            # 用 Semantic Scholar 搜标题
            try:
                s2_results = await semantic_scholar.search(title, limit=5, api_key=s2_key)
                sources_checked.append("semantic_scholar")
                for r in s2_results:
                    if _title_match(r.get("title", ""), title):
                        if year and r.get("year") and r["year"] != year:
                            continue
                        if authors and not _authors_overlap(r.get("authors", []), authors):
                            continue
                        sources_confirmed.append("semantic_scholar")
                        verified_metadata["semantic_scholar"] = {
                            "title": r.get("title"),
                            "authors": r.get("authors"),
                            "year": r.get("year"),
                            "doi": r.get("doi"),
                        }
                        break
            except Exception as e:
                sources_checked.append("semantic_scholar")
                logger.warning(f"S2 标题搜索失败: {e}")

            # 用 CrossRef 搜标题
            try:
                cr_results = await crossref.search(title, limit=5)
                sources_checked.append("crossref")
                for r in cr_results:
                    if _title_match(r.get("title", ""), title):
                        if year and r.get("year") and r["year"] != year:
                            continue
                        sources_confirmed.append("crossref")
                        verified_metadata["crossref"] = {
                            "title": r.get("title"),
                            "authors": r.get("authors"),
                            "year": r.get("year"),
                            "doi": r.get("doi"),
                        }
                        break
            except Exception as e:
                sources_checked.append("crossref")
                logger.warning(f"CrossRef 标题搜索失败: {e}")

        else:
            return {
                "status": "unverified",
                "confidence": 0.0,
                "sources_checked": [],
                "sources_confirmed": [],
                "is_retracted": False,
                "retraction_source": None,
                "verified_metadata": {},
                "discrepancies": ["未提供 DOI 或标题，无法验证"],
            }

        # ── 交叉比对：检查不一致 ──
        titles = {}
        years = {}
        for src, meta in verified_metadata.items():
            if meta.get("title"):
                titles[src] = meta["title"]
            if meta.get("year"):
                years[src] = meta["year"]

        unique_titles = set(t.lower().strip() for t in titles.values())
        if len(unique_titles) > 1:
            discrepancies.append(f"标题不一致: {titles}")

        unique_years = set(years.values())
        if len(unique_years) > 1:
            discrepancies.append(f"年份不一致: {years}")

        status, confidence = _evaluate_status(
            is_retracted=is_retracted,
            sources_confirmed=len(sources_confirmed),
            sources_checked=len(sources_checked),
            has_discrepancies=bool(discrepancies),
        )

        return {
            "status": status,
            "confidence": confidence,
            "sources_checked": sources_checked,
            "sources_confirmed": sources_confirmed,
            "is_retracted": is_retracted,
            "retraction_source": retraction_source,
            "verified_metadata": verified_metadata,
            "discrepancies": discrepancies,
        }


def _title_match(a: str, b: str) -> bool:
    """模糊标题匹配：忽略大小写和标点后比较。"""
    import re
    def normalize(s: str) -> str:
        return re.sub(r"[^a-z0-9\s]", "", s.lower().strip())
    return normalize(a) == normalize(b)


def _authors_overlap(candidates: list, expected: list[str]) -> bool:
    """检查作者列表是否有交集（至少第一作者匹配）。

    candidates 可能是 [str] 或 [{"name": ...}]。
    """
    def extract_names(lst: list) -> set[str]:
        names = set()
        for item in lst:
            if isinstance(item, dict):
                name = item.get("name", "")
            else:
                name = str(item)
            # 只取 family name（最后一个单词）做模糊匹配
            parts = name.strip().split()
            if parts:
                names.add(parts[-1].lower())
        return names

    cand_names = extract_names(candidates)
    exp_names = extract_names(expected)
    # 至少有一个 family name 交集
    return bool(cand_names & exp_names)


def _evaluate_status(
    *,
    is_retracted: bool,
    sources_confirmed: int,
    sources_checked: int,
    has_discrepancies: bool,
) -> tuple[str, float]:
    """Pure status evaluation logic for citation verification."""
    if is_retracted:
        status = "retracted"
        confidence = 1.0
    elif sources_confirmed >= 2:
        status = "verified"
        confidence = sources_confirmed / max(sources_checked, 1)
    elif sources_confirmed == 1:
        status = "unverified"  # 单源不足以确认
        confidence = 0.5  # 保留弱信号
    else:
        status = "unverified"
        confidence = 0.0

    if has_discrepancies:
        confidence *= 0.8

    return status, round(confidence, 2)
