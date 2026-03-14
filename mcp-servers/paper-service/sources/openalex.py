"""OpenAlex API 数据源

- 论文元数据 + cited_by_percentile
- is_retracted 撤稿检查
- primary_location（OA 发现）

官方文档: https://docs.openalex.org/
速率限制: 100k/天 (需 email)
"""

from __future__ import annotations

import httpx

BASE_URL = "https://api.openalex.org"


def _parse_work(work: dict) -> dict:
    """将 OpenAlex work 转换为统一格式。"""
    # 作者
    authors = []
    for authorship in work.get("authorships", []):
        author = authorship.get("author", {})
        name = author.get("display_name", "")
        if name:
            authors.append(name)

    # 主要位置（OA 检查）
    primary = work.get("primary_location") or {}
    source = primary.get("source") or {}

    # OA 信息
    oa = work.get("open_access", {})
    oa_url = oa.get("oa_url")

    return {
        "openalex_id": work.get("id"),
        "doi": (work.get("doi") or "").replace("https://doi.org/", ""),
        "title": work.get("title", ""),
        "authors": authors,
        "year": work.get("publication_year"),
        "venue": source.get("display_name", ""),
        "cited_by_count": work.get("cited_by_count", 0),
        "cited_by_percentile": work.get("cited_by_percentile_year", {}),
        "is_retracted": work.get("is_retracted", False),
        "is_oa": oa.get("is_oa", False),
        "oa_url": oa_url,
        "type": work.get("type"),
    }


async def search(
    query: str,
    *,
    limit: int = 20,
    email: str | None = None,
    year_range: tuple[int, int] | None = None,
) -> list[dict]:
    """搜索 OpenAlex works。"""
    params: dict = {
        "search": query,
        "per_page": min(limit, 200),
        "select": "id,doi,title,authorships,publication_year,"
                  "primary_location,open_access,cited_by_count,"
                  "cited_by_percentile_year,is_retracted,type",
    }
    if email:
        params["mailto"] = email
    if year_range:
        params["filter"] = (
            f"publication_year:{year_range[0]}-{year_range[1]}"
        )

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{BASE_URL}/works", params=params)
        resp.raise_for_status()
        data = resp.json()

    return [_parse_work(w) for w in data.get("results", [])]


async def get_by_doi(
    doi: str, *, email: str | None = None
) -> dict | None:
    """通过 DOI 获取 OpenAlex work（用于验证 + 撤稿检查）。"""
    params: dict = {
        "select": "id,doi,title,authorships,publication_year,"
                  "primary_location,open_access,cited_by_count,"
                  "cited_by_percentile_year,is_retracted,type",
    }
    if email:
        params["mailto"] = email

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{BASE_URL}/works/https://doi.org/{doi}", params=params
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return _parse_work(resp.json())
