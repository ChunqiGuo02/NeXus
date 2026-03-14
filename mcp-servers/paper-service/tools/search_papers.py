"""search_papers MCP Tool

多源并发搜索论文，返回去重后的统一格式结果。
"""

from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Awaitable
from typing import Any

from fastmcp import FastMCP

from sources import semantic_scholar, arxiv_source, crossref, openalex

import json
from pathlib import Path

_CONFIG_PATH = Path.home() / ".aria" / "global_config.json"


def _get_s2_key() -> str | None:
    try:
        if _CONFIG_PATH.exists():
            cfg = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
            return cfg.get("semantic_scholar_key")
    except Exception:
        pass
    return None


def _make_id(doi: str | None, arxiv_id: str | None, title: str) -> str:
    """生成去重 ID：优先 DOI > arXiv ID > title hash。"""
    if doi:
        return hashlib.sha256(doi.lower().encode()).hexdigest()[:16]
    if arxiv_id:
        return hashlib.sha256(arxiv_id.lower().encode()).hexdigest()[:16]
    return hashlib.sha256(title.lower().strip().encode()).hexdigest()[:16]


def _normalize(paper: dict, source: str) -> dict:
    """将各数据源的结果统一为标准格式。"""
    doi = paper.get("doi") or None
    arxiv_id = paper.get("arxiv_id") or None

    # Semantic Scholar 的 externalIds 中可能有 DOI/ArXiv
    ext_ids = paper.get("externalIds") or {}
    if not doi and ext_ids.get("DOI"):
        doi = ext_ids["DOI"]
    if not arxiv_id and ext_ids.get("ArXiv"):
        arxiv_id = ext_ids["ArXiv"]

    title = paper.get("title", "")

    # 作者统一为字符串列表
    raw_authors = paper.get("authors", [])
    if raw_authors and isinstance(raw_authors[0], dict):
        authors = [a.get("name", "") for a in raw_authors]
    elif isinstance(raw_authors, str):
        authors = [raw_authors]
    else:
        authors = list(raw_authors)

    return {
        "id": _make_id(doi, arxiv_id, title),
        "doi": doi,
        "arxiv_id": arxiv_id,
        "title": title,
        "authors": authors,
        "year": paper.get("year") or paper.get("publication_year"),
        "venue": paper.get("venue", ""),
        "abstract": paper.get("abstract", ""),
        "cited_by_count": paper.get("cited_by_count")
                          or paper.get("citationCount")
                          or paper.get("is_referenced_by_count", 0),
        "is_oa": paper.get("is_oa") or paper.get("isOpenAccess", False),
        "pdf_url": paper.get("pdf_url")
                   or paper.get("oa_url")
                   or (paper.get("openAccessPdf") or {}).get("url"),
        "source": source,
    }


def _dedup(papers: list[dict]) -> list[dict]:
    """基于 id 去重，保留 cited_by_count 最高的。"""
    seen: dict[str, dict] = {}
    for p in papers:
        pid = p["id"]
        if pid not in seen or p["cited_by_count"] > seen[pid]["cited_by_count"]:
            seen[pid] = p
    return list(seen.values())


def register(mcp_instance: FastMCP) -> None:
    @mcp_instance.tool()
    async def search_papers(
        query: str,
        sources: list[str] | None = None,
        max_results: int = 50,
        year_range: str | None = None,
        sort_by: str = "relevance",
    ) -> dict[str, Any]:
        """多源并发搜索学术论文。

        Args:
            query: 搜索关键词
            sources: 指定数据源列表，默认全部。可选: semantic_scholar, arxiv, crossref, openalex
            max_results: 每个数据源的最大结果数
            year_range: 年份范围，格式 "2020-2026"
            sort_by: 排序方式: relevance | citation_count | date

        Returns:
            去重后的论文列表 + 搜索统计
        """
        # 解析 year_range
        yr = None
        if year_range and "-" in year_range:
            parts = year_range.split("-")
            yr = (int(parts[0]), int(parts[1]))

        active_sources = sources or [
            "semantic_scholar", "arxiv", "crossref", "openalex"
        ]
        per_source = max(max_results // len(active_sources), 10)

        # 构建并发任务
        tasks: list[Awaitable[list[dict[str, Any]]]] = []
        source_names = []

        s2_key = _get_s2_key()

        if "semantic_scholar" in active_sources:
            tasks.append(
                semantic_scholar.search(
                    query, limit=per_source, year_range=yr, api_key=s2_key
                )
            )
            source_names.append("semantic_scholar")

        if "arxiv" in active_sources:
            tasks.append(
                arxiv_source.search(query, limit=per_source, sort_by=sort_by)
            )
            source_names.append("arxiv")

        if "crossref" in active_sources:
            tasks.append(crossref.search(query, limit=per_source))
            source_names.append("crossref")

        if "openalex" in active_sources:
            tasks.append(
                openalex.search(query, limit=per_source, year_range=yr)
            )
            source_names.append("openalex")

        # 并发执行，容忍单个源失败
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        all_papers = []
        errors = []
        for name, result in zip(source_names, raw_results):
            if isinstance(result, BaseException):
                errors.append(f"{name}: {result}")
                continue
            if not isinstance(result, list):
                errors.append(f"{name}: invalid response type {type(result).__name__}")
                continue
            for paper in result:
                if not isinstance(paper, dict):
                    errors.append(
                        f"{name}: invalid paper item type {type(paper).__name__}"
                    )
                    continue
                all_papers.append(_normalize(paper, name))

        # 去重
        deduped = _dedup(all_papers)

        # 排序
        if sort_by == "citation_count":
            deduped.sort(key=lambda p: p["cited_by_count"], reverse=True)
        elif sort_by == "date":
            deduped.sort(
                key=lambda p: p.get("year") or 0, reverse=True
            )

        return {
            "total": len(deduped),
            "papers": deduped[:max_results],
            "sources_queried": source_names,
            "errors": errors,
        }
