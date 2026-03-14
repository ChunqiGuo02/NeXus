"""DataCite API 数据源

- 数据集 / 软件 DOI 元数据查询
- 用于补充非论文类学术产出的引用验证

官方文档: https://support.datacite.org/docs/api
速率限制: 无硬限制
"""

from __future__ import annotations

import httpx

BASE_URL = "https://api.datacite.org"


async def get_by_doi(doi: str) -> dict | None:
    """通过 DOI 获取 DataCite 元数据（数据集/软件）。"""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{BASE_URL}/dois/{doi}")
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()

    attrs = data.get("data", {}).get("attributes", {})
    if not attrs:
        return None

    # 作者
    creators = attrs.get("creators", [])
    authors = [c.get("name", "") for c in creators]

    return {
        "doi": attrs.get("doi"),
        "title": (attrs.get("titles") or [{}])[0].get("title", ""),
        "authors": authors,
        "year": attrs.get("publicationYear"),
        "type": attrs.get("types", {}).get("resourceTypeGeneral", ""),
        "publisher": attrs.get("publisher", ""),
        "url": attrs.get("url"),
    }
