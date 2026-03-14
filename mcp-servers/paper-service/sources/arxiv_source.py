"""arXiv API 数据源

- 搜索预印本
- 获取论文元数据 + PDF 直链

官方文档: https://info.arxiv.org/help/api/
速率限制: ~3 秒/请求（建议）
"""

from __future__ import annotations

import re

import feedparser  # type: ignore[import-untyped]
import httpx

BASE_URL = "https://export.arxiv.org/api/query"


def _parse_entry(entry: dict) -> dict:
    """将 feedparser entry 转换为统一格式。"""
    # 提取 arXiv ID（去掉版本号）
    arxiv_id_raw = entry.get("id", "")
    arxiv_id = re.sub(r"v\d+$", "", arxiv_id_raw.split("/abs/")[-1])

    # PDF 链接
    pdf_url = None
    for link in entry.get("links", []):
        if link.get("type") == "application/pdf":
            pdf_url = link["href"]
            break
    if not pdf_url and arxiv_id:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    # 作者
    authors = [a.get("name", "") for a in entry.get("authors", [])]

    # 年份
    published = entry.get("published", "")
    year = int(published[:4]) if len(published) >= 4 else None

    return {
        "arxiv_id": arxiv_id,
        "title": entry.get("title", "").replace("\n", " ").strip(),
        "abstract": entry.get("summary", "").strip(),
        "authors": authors,
        "year": year,
        "published": published,
        "pdf_url": pdf_url,
        "primary_category": entry.get("arxiv_primary_category", {}).get("term"),
        "categories": [t.get("term") for t in entry.get("tags", [])],
    }


async def search(
    query: str,
    *,
    limit: int = 20,
    sort_by: str = "relevance",
) -> list[dict]:
    """搜索 arXiv 论文。"""
    sort_map = {
        "relevance": "relevance",
        "date": "submittedDate",
        "citation_count": "relevance",  # arXiv 不支持按引用排序
    }
    params: dict[str, str | int] = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": min(limit, 100),
        "sortBy": sort_map.get(sort_by, "relevance"),
        "sortOrder": "descending",
    }

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(BASE_URL, params=params)
        resp.raise_for_status()

    feed = feedparser.parse(resp.text)
    return [_parse_entry(e) for e in feed.entries]


async def get_paper(arxiv_id: str) -> dict | None:
    """通过 arXiv ID 获取单篇论文元数据。"""
    params: dict[str, str | int] = {"id_list": arxiv_id, "max_results": 1}

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(BASE_URL, params=params)
        resp.raise_for_status()

    feed = feedparser.parse(resp.text)
    if not feed.entries:
        return None
    return _parse_entry(feed.entries[0])
