"""Semantic Scholar API 数据源

- 搜索论文（关键词/DOI/arXiv ID）
- 获取引用关系
- 获取论文详情

官方文档: https://api.semanticscholar.org/api-docs/
无 key: 100 次/5 分钟; 有 key: 100 次/秒
"""

from __future__ import annotations

from shared import get_client, with_retry

BASE_URL = "https://api.semanticscholar.org/graph/v1"

PAPER_FIELDS = (
    "paperId,externalIds,title,abstract,year,venue,"
    "citationCount,referenceCount,isOpenAccess,openAccessPdf,"
    "authors.name,publicationDate"
)


@with_retry(max_attempts=3, backoff=[1.0, 5.0, 15.0])
async def search(
    query: str,
    *,
    limit: int = 20,
    year_range: tuple[int, int] | None = None,
    api_key: str | None = None,
) -> list[dict]:
    """关键词搜索论文。"""
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key

    params: dict = {
        "query": query,
        "limit": min(limit, 100),
        "fields": PAPER_FIELDS,
    }
    if year_range:
        params["year"] = f"{year_range[0]}-{year_range[1]}"

    client = get_client()
    resp = await client.get(
        f"{BASE_URL}/paper/search", params=params, headers=headers
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", [])


@with_retry(max_attempts=3, backoff=[1.0, 5.0, 15.0])
async def get_paper(
    identifier: str, *, api_key: str | None = None
) -> dict | None:
    """通过 S2 Paper ID / DOI / arXiv ID 获取论文详情。

    identifier 格式: "DOI:10.xxx" 或 "ARXIV:2301.12345" 或直接 S2 ID
    """
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key

    client = get_client()
    resp = await client.get(
        f"{BASE_URL}/paper/{identifier}",
        params={"fields": PAPER_FIELDS},
        headers=headers,
    )
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


@with_retry(max_attempts=3, backoff=[1.0, 5.0, 15.0])
async def get_citations(
    identifier: str,
    *,
    direction: str = "both",
    limit: int = 50,
    api_key: str | None = None,
) -> dict:
    """获取引用/被引关系。"""
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key

    result: dict = {"references": [], "citations": []}
    fields = "paperId,externalIds,title,year,authors.name"

    client = get_client()

    if direction in ("references", "both"):
        resp = await client.get(
            f"{BASE_URL}/paper/{identifier}/references",
            params={"fields": fields, "limit": limit},
            headers=headers,
        )
        if resp.status_code == 200:
            result["references"] = [
                r["citedPaper"]
                for r in resp.json().get("data", [])
                if r.get("citedPaper")
            ]

    if direction in ("citations", "both"):
        resp = await client.get(
            f"{BASE_URL}/paper/{identifier}/citations",
            params={"fields": fields, "limit": limit},
            headers=headers,
        )
        if resp.status_code == 200:
            result["citations"] = [
                r["citingPaper"]
                for r in resp.json().get("data", [])
                if r.get("citingPaper")
            ]

    return result
