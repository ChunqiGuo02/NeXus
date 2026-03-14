"""影子图书馆数据源（可配置插件）

- Sci-Hub: 通过 DOI 获取论文 PDF
- LibGen: 通过 DOI/标题搜索

TLS 策略: 支持 strict / strict_then_fallback / unsafe 三种模式。
默认 strict_then_fallback（先严格校验，失败后降级）。

此模块仅在 config.shadow_library_enabled = True 时启用。
开源项目 disclaimer: 此功能仅供学术研究参考，用户需自行承担法律责任。
"""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx

logger = logging.getLogger("paper-service")

SCIHUB_MIRRORS = [
    "sci-hub.se",
    "sci-hub.st",
    "sci-hub.ru",
    "sci-hub.ren",
]


def _is_cert_verification_error(exc: BaseException) -> bool:
    """Return True when exception chain indicates certificate verification failure."""
    markers = (
        "sslcertverificationerror",
        "certificate verify failed",
        "certificate_verify_failed",
        "certificate verify error",
    )

    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        text = f"{type(current).__name__}: {current}".lower()
        if any(marker in text for marker in markers):
            return True
        current = current.__cause__ or current.__context__
    return False


async def _fetch_from_scihub_with_verify(
    doi: str,
    *,
    verify: bool,
) -> tuple[dict[str, Any], BaseException | None]:
    """Fetch DOI from Sci-Hub mirrors with a fixed TLS setting."""
    last_error: BaseException | None = None

    try:
        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            verify=verify,
        ) as client:
            for mirror in SCIHUB_MIRRORS:
                try:
                    url = f"https://{mirror}/{doi}"
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        continue

                    html = resp.text
                    pattern = r'(?:iframe|embed)[^>]+src=["\']([^"\']+\.pdf[^"\']*)'
                    match = re.search(pattern, html, re.IGNORECASE)
                    if match:
                        pdf_url = match.group(1)
                        if pdf_url.startswith("//"):
                            pdf_url = "https:" + pdf_url
                        return {
                            "success": True,
                            "pdf_url": pdf_url,
                            "mirror": mirror,
                        }, None

                    if "application/pdf" in resp.headers.get("content-type", ""):
                        return {
                            "success": True,
                            "pdf_url": url,
                            "mirror": mirror,
                        }, None

                except (httpx.HTTPError, httpx.ConnectError) as e:
                    last_error = e
                    continue
    except Exception as e:
        last_error = e

    return {"success": False, "pdf_url": None, "mirror": None}, last_error


async def fetch_from_scihub(
    doi: str,
    *,
    tls_mode: str = "strict_then_fallback",
) -> dict:
    """通过 Sci-Hub 获取论文 PDF URL。

    tls_mode:
        "strict" — 严格 TLS，失败即放弃
        "strict_then_fallback" — 先严格，证书错误时降级
        "unsafe" — 直接跳过验证（不推荐）
    """
    if tls_mode == "unsafe":
        logger.warning("Sci-Hub: TLS 校验已降级 (verify=False)")
        result, _ = await _fetch_from_scihub_with_verify(doi, verify=False)
        return result

    strict_result, strict_error = await _fetch_from_scihub_with_verify(doi, verify=True)
    if strict_result.get("success"):
        return strict_result

    if tls_mode == "strict":
        return strict_result

    # strict_then_fallback: only fallback when strict mode failed due cert verification.
    if strict_error and _is_cert_verification_error(strict_error):
        logger.info("Sci-Hub: TLS 严格校验失败（证书错误），尝试降级")
        logger.warning("Sci-Hub: TLS 校验已降级 (verify=False)")
        fallback_result, _ = await _fetch_from_scihub_with_verify(doi, verify=False)
        return fallback_result

    return strict_result


async def fetch_from_libgen(doi: str) -> dict:
    """通过 LibGen 获取论文 PDF URL。"""
    search_url = "https://libgen.rs/scimag/"
    params = {"q": doi}

    try:
        async with httpx.AsyncClient(
            timeout=30, follow_redirects=True
        ) as client:
            resp = await client.get(search_url, params=params)
            if resp.status_code != 200:
                return {"success": False, "download_url": None}

            html = resp.text
            pattern = r'href=["\']([^"\']*(?:get|download)[^"\']*)'
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return {"success": True, "download_url": match.group(1)}

    except (httpx.HTTPError, httpx.ConnectError):
        pass

    return {"success": False, "download_url": None}
