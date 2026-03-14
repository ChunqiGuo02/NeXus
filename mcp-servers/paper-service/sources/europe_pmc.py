"""Europe PMC API 数据源

- 生物医学 OA 全文搜索
- 通过 DOI/PMID 查找全文

官方文档: https://europepmc.org/RestfulWebService
速率限制: 合理使用
"""

from __future__ import annotations

import httpx

BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"


async def search(
    query: str,
    *,
    limit: int = 20,
) -> list[dict]:
    """搜索 Europe PMC 论文。"""
    params: dict[str, str | int] = {
        "query": query,
        "pageSize": min(limit, 100),
        "resultType": "core",
        "format": "json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{BASE_URL}/search", params=params)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("resultList", {}).get("result", []):
        results.append({
            "pmid": item.get("pmid"),
            "pmcid": item.get("pmcid"),
            "doi": item.get("doi"),
            "title": item.get("title", ""),
            "authors": item.get("authorString", ""),
            "year": item.get("pubYear"),
            "journal": item.get("journalTitle", ""),
            "is_open_access": item.get("isOpenAccess") == "Y",
            "full_text_url": (
                f"https://europepmc.org/articles/{item['pmcid']}"
                if item.get("pmcid")
                else None
            ),
        })
    return results


async def get_by_doi(doi: str) -> dict | None:
    """通过 DOI 在 Europe PMC 查找。"""
    params: dict[str, str | int] = {
        "query": f'DOI:"{doi}"',
        "pageSize": 1,
        "resultType": "core",
        "format": "json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{BASE_URL}/search", params=params)
        if resp.status_code != 200:
            return None
        data = resp.json()

    results = data.get("resultList", {}).get("result", [])
    if not results:
        return None

    item = results[0]
    return {
        "pmcid": item.get("pmcid"),
        "is_open_access": item.get("isOpenAccess") == "Y",
        "full_text_url": (
            f"https://europepmc.org/articles/{item['pmcid']}"
            if item.get("pmcid")
            else None
        ),
    }
