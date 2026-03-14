"""Unpaywall API 数据源

- 通过 DOI 查询 OA 版本
- 返回 best OA location（PDF URL）

官方文档: https://unpaywall.org/products/api
速率限制: 100k/天 (需 email)
"""

from __future__ import annotations

import httpx

BASE_URL = "https://api.unpaywall.org/v2"


async def find_oa(doi: str, *, email: str) -> dict | None:
    """通过 DOI 查找 OA 版本。

    返回:
        {
            "is_oa": bool,
            "best_oa_url": str | None,     # PDF 直链
            "oa_status": str,               # gold/green/hybrid/bronze/closed
            "journal_is_oa": bool,
        }
    """
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{BASE_URL}/{doi}",
            params={"email": email},
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()

    best_location = data.get("best_oa_location") or {}
    return {
        "is_oa": data.get("is_oa", False),
        "best_oa_url": best_location.get("url_for_pdf")
                       or best_location.get("url"),
        "oa_status": data.get("oa_status", "closed"),
        "journal_is_oa": data.get("journal_is_oa", False),
    }
