"""CORE API 数据源

- OA 全文搜索
- 通过 DOI 查找 OA 全文

官方文档: https://core.ac.uk/documentation/api
速率限制: 10 次/10 秒 (免费 API key)
"""

from __future__ import annotations

import httpx

BASE_URL = "https://api.core.ac.uk/v3"


async def search(
    query: str,
    *,
    limit: int = 10,
    api_key: str | None = None,
) -> list[dict]:
    """搜索 CORE OA 论文。"""
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    params: dict[str, str | int] = {"q": query, "limit": min(limit, 100)}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{BASE_URL}/search/works", params=params, headers=headers
        )
        if resp.status_code != 200:
            return []
        data = resp.json()

    results = []
    for item in data.get("results", []):
        results.append({
            "core_id": item.get("id"),
            "doi": item.get("doi"),
            "title": item.get("title", ""),
            "authors": [
                a.get("name", "") for a in item.get("authors", [])
            ],
            "year": item.get("yearPublished"),
            "abstract": item.get("abstract", ""),
            "download_url": item.get("downloadUrl"),
            "full_text_available": bool(item.get("fullText")),
        })
    return results


async def get_by_doi(
    doi: str, *, api_key: str | None = None
) -> dict | None:
    """通过 DOI 在 CORE 中查找 OA 全文链接。"""
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    params: dict[str, str | int] = {"q": f'doi:"{doi}"', "limit": 1}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{BASE_URL}/search/works",
            params=params,
            headers=headers,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()

    results = data.get("results", [])
    if not results:
        return None

    item = results[0]
    return {
        "core_id": item.get("id"),
        "download_url": item.get("downloadUrl"),
        "full_text_available": bool(item.get("fullText")),
    }
