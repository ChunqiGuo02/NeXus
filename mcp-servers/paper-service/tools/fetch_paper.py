"""fetch_paper MCP Tool

五级瀑布流获取论文全文。
每个 tier 独立异常隔离，单源失败不中断整体流程。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from sources import (
    arxiv_source,
    unpaywall,
    core_api,
    europe_pmc,
    openalex,
    shadow_library,
)

logger = logging.getLogger("paper-service")

GLOBAL_CONFIG_PATH = Path.home() / ".nexus" / "global_config.json"


def _load_config() -> dict:
    if GLOBAL_CONFIG_PATH.exists():
        return json.loads(GLOBAL_CONFIG_PATH.read_text(encoding="utf-8"))
    return {
        "shadow_library_enabled": True,
        "shadow_tls_mode": "strict_then_fallback",
        "email": None,
    }


def register(mcp_instance: FastMCP) -> None:
    @mcp_instance.tool()
    async def fetch_paper(
        identifier: str,
        project: str | None = None,
    ) -> dict[str, Any]:
        """五级瀑布流获取论文。

        Args:
            identifier: DOI (如 "10.1038/nature12373") 或 arXiv ID (如 "2301.12345")
            project: 项目名（暂未生效，保留兼容）

        Returns:
            {
                "access_state": str,
                "pdf_url": str | None,
                "access_source": str,
                "metadata": dict,
                "message": str,
                "errors": list[str],
            }
        """
        if project is not None:
            logger.info("fetch_paper: project 参数当前未生效，后续版本将落地")

        config = _load_config()
        email = config.get("email")
        is_arxiv = not identifier.startswith("10.")

        result: dict[str, Any] = {
            "access_state": "unavailable",
            "pdf_url": None,
            "access_source": "none",
            "metadata": {},
            "message": "",
            "errors": [],
        }

        # ── Tier 1: arXiv fast path ──
        if is_arxiv:
            try:
                arxiv_id = identifier.replace("arxiv:", "").replace("ARXIV:", "")
                paper = await arxiv_source.get_paper(arxiv_id)
                if paper:
                    result["metadata"] = paper
                    result["pdf_url"] = paper.get("pdf_url")
                    result["access_state"] = "oa_fulltext"
                    result["access_source"] = "arxiv"
                    result["message"] = (
                        f"arXiv 论文，可通过 alphaxiv-paper-lookup 获取结构化 Markdown，"
                        f"或直接下载 PDF: {result['pdf_url']}"
                    )
                    return result
            except Exception as e:
                result["errors"].append(f"[Tier1:arXiv] {type(e).__name__}: {e}")
                logger.warning(f"Tier1 arXiv 失败: {e}")

        doi = identifier if identifier.startswith("10.") else None

        # ── Tier 2: OA 合法源 ──
        if doi and email:
            # 2a: Unpaywall
            try:
                oa_info = await unpaywall.find_oa(doi, email=email)
                if oa_info and oa_info.get("is_oa") and oa_info.get("best_oa_url"):
                    result["pdf_url"] = oa_info["best_oa_url"]
                    result["access_state"] = "oa_fulltext"
                    result["access_source"] = "unpaywall"
                    result["message"] = f"OA 全文可用 (via Unpaywall, {oa_info.get('oa_status')})"
                    return result
            except Exception as e:
                result["errors"].append(f"[Tier2:Unpaywall] {type(e).__name__}: {e}")
                logger.warning(f"Tier2 Unpaywall 失败: {e}")

            # 2b: OpenAlex
            try:
                oalex = await openalex.get_by_doi(doi, email=email)
                if oalex:
                    result["metadata"] = oalex
                    if oalex.get("is_oa") and oalex.get("oa_url"):
                        result["pdf_url"] = oalex["oa_url"]
                        result["access_state"] = "oa_fulltext"
                        result["access_source"] = "openalex"
                        result["message"] = "OA 全文可用 (via OpenAlex)"
                        return result
            except Exception as e:
                result["errors"].append(f"[Tier2:OpenAlex] {type(e).__name__}: {e}")
                logger.warning(f"Tier2 OpenAlex 失败: {e}")

        if doi:
            # 2c: CORE
            try:
                core_info = await core_api.get_by_doi(doi)
                if core_info and core_info.get("download_url"):
                    result["pdf_url"] = core_info["download_url"]
                    result["access_state"] = "repository_fulltext"
                    result["access_source"] = "core"
                    result["message"] = "OA 仓库版本可用 (via CORE)"
                    return result
            except Exception as e:
                result["errors"].append(f"[Tier2:CORE] {type(e).__name__}: {e}")
                logger.warning(f"Tier2 CORE 失败: {e}")

            # 2d: Europe PMC
            try:
                pmc_info = await europe_pmc.get_by_doi(doi)
                if pmc_info and pmc_info.get("is_open_access") and pmc_info.get("full_text_url"):
                    result["pdf_url"] = pmc_info["full_text_url"]
                    result["access_state"] = "repository_fulltext"
                    result["access_source"] = "europe_pmc"
                    result["message"] = "OA 全文可用 (via Europe PMC)"
                    return result
            except Exception as e:
                result["errors"].append(f"[Tier2:EuropePMC] {type(e).__name__}: {e}")
                logger.warning(f"Tier2 Europe PMC 失败: {e}")

        # ── Tier 3: 影子图书馆 ──
        if doi and config.get("shadow_library_enabled", True):
            tls_mode = config.get("shadow_tls_mode", "strict_then_fallback")

            # 3a: Sci-Hub
            try:
                scihub = await shadow_library.fetch_from_scihub(doi, tls_mode=tls_mode)
                if scihub.get("success"):
                    result["pdf_url"] = scihub["pdf_url"]
                    result["access_state"] = "shadow_fulltext"
                    result["access_source"] = f"sci-hub ({scihub.get('mirror')})"
                    result["message"] = "全文已通过 Sci-Hub 获取"
                    return result
            except Exception as e:
                result["errors"].append(f"[Tier3:SciHub] {type(e).__name__}: {e}")
                logger.warning(f"Tier3 Sci-Hub 失败: {e}")

            # 3b: LibGen
            try:
                libgen = await shadow_library.fetch_from_libgen(doi)
                if libgen.get("success"):
                    result["pdf_url"] = libgen["download_url"]
                    result["access_state"] = "shadow_fulltext"
                    result["access_source"] = "libgen"
                    result["message"] = "全文已通过 LibGen 获取"
                    return result
            except Exception as e:
                result["errors"].append(f"[Tier3:LibGen] {type(e).__name__}: {e}")
                logger.warning(f"Tier3 LibGen 失败: {e}")

        # ── Tier 4 & 5: 降级 ──
        try:
            if doi and email:
                oalex = result.get("metadata") or await openalex.get_by_doi(doi, email=email)
                if oalex and oalex.get("title"):
                    result["metadata"] = oalex
                    result["access_state"] = "abstract_only"
                    result["access_source"] = "openalex_metadata"
                    result["message"] = (
                        "Warning: 无法获取全文。可选操作:\n"
                        "1. 从学校数据库手动下载 PDF 放入 raw_pdfs/ 目录\n"
                        f"2. 直接搜索: https://scholar.google.com/scholar?q={doi}"
                    )
                    return result
        except Exception as e:
            result["errors"].append(f"[Tier5:Fallback] {type(e).__name__}: {e}")

        result["access_state"] = "metadata_only" if result["metadata"] else "unavailable"
        result["access_source"] = "none"
        result["message"] = "X 未找到此论文的任何可用版本"
        return result
