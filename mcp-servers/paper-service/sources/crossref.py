"""CrossRef API 数据源

- DOI 元数据验证
- 引用关系
- TDM/License 信息

官方文档: https://api.crossref.org/
速率限制: ~50/s (polite pool, 需 email in User-Agent)
"""

from __future__ import annotations

import httpx

BASE_URL = "https://api.crossref.org"


def _polite_headers(email: str | None) -> dict:
    """构造 polite pool 的 User-Agent。"""
    ua = "NeXus/0.1 (https://github.com/ChunqiGuo02/NeXus)"
    if email:
        ua += f" (mailto:{email})"
    return {"User-Agent": ua}


def _parse_item(item: dict) -> dict:
    """将 CrossRef work item 转换为统一格式。"""
    # 标题
    titles = item.get("title", [])
    title = titles[0] if titles else ""

    # 作者
    authors = []
    for a in item.get("author", []):
        name_parts = [a.get("given", ""), a.get("family", "")]
        authors.append(" ".join(p for p in name_parts if p))

    # 年份
    date_parts = item.get("published-print", item.get("published-online", {}))
    year = None
    if date_parts and date_parts.get("date-parts"):
        year = date_parts["date-parts"][0][0]

    return {
        "doi": item.get("DOI"),
        "title": title,
        "authors": authors,
        "year": year,
        "venue": item.get("container-title", [""])[0],
        "type": item.get("type"),
        "is_referenced_by_count": item.get("is-referenced-by-count", 0),
        "license": [lic.get("URL") for lic in item.get("license", [])],
        "issn": item.get("ISSN", []),
    }


async def search(
    query: str,
    *,
    limit: int = 20,
    email: str | None = None,
) -> list[dict]:
    """通过关键词搜索 CrossRef works。"""
    params: dict[str, str | int] = {
        "query": query,
        "rows": min(limit, 100),
        "select": "DOI,title,author,published-print,published-online,"
                  "container-title,type,is-referenced-by-count,license,ISSN",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{BASE_URL}/works",
            params=params,
            headers=_polite_headers(email),
        )
        resp.raise_for_status()
        data = resp.json()

    items = data.get("message", {}).get("items", [])
    return [_parse_item(i) for i in items]


async def get_by_doi(doi: str, *, email: str | None = None) -> dict | None:
    """通过 DOI 获取元数据（用于引用验证）。"""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{BASE_URL}/works/{doi}",
            headers=_polite_headers(email),
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()

    item = data.get("message", {})
    return _parse_item(item) if item else None
