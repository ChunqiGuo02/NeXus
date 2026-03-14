"""download_pdf MCP Tool

下载 PDF 到 workspace 的 raw_pdfs/ 目录。
含路径穿越防护和 TLS 校验。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import httpx

from fastmcp import FastMCP
from shared import get_client

logger = logging.getLogger("paper-service")


def _sanitize_filename(filename: str) -> str | None:
    """校验并清理文件名，拒绝路径穿越。

    返回 None 表示不合法。
    """
    # 拒绝绝对路径
    if Path(filename).is_absolute():
        return None
    # Reject path separators.
    if "/" in filename or "\\" in filename:
        return None
    # 拒绝 ..
    if ".." in filename:
        return None
    # 归一化：只保留文件名部分
    clean = Path(filename).name
    if not clean or clean.startswith("."):
        return None
    return clean


def register(mcp_instance: FastMCP) -> None:
    @mcp_instance.tool()
    async def download_pdf(
        url: str,
        filename: str,
        project_dir: str,
    ) -> dict[str, Any]:
        """下载 PDF 文件到指定项目目录。

        Args:
            url: PDF 下载链接
            filename: 保存文件名 (如 "attention_2023.pdf")
            project_dir: 项目工作区路径 (如 "workspace/my-project")

        Returns:
            {"success": bool, "path": str, "size_bytes": int, "message": str}
        """
        # 路径穿越防护
        clean_name = _sanitize_filename(filename)
        if clean_name is None:
            return {
                "success": False,
                "path": "",
                "size_bytes": 0,
                "message": f"非法文件名: {filename!r}（禁止路径穿越、绝对路径和目录分隔符）",
            }

        save_dir = Path(project_dir).resolve() / "raw_pdfs"
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = (save_dir / clean_name).resolve()

        # Secondary guard after resolve(): target must remain under raw_pdfs.
        if not str(save_path).startswith(str(save_dir)):
            return {
                "success": False,
                "path": "",
                "size_bytes": 0,
                "message": "Path traversal detected: target path is outside raw_pdfs",
            }

        try:
            client = get_client(verify=True)  # TLS 严格校验
            resp = await client.get(url)
            resp.raise_for_status()

            # 验证是 PDF
            content_type = resp.headers.get("content-type", "")
            if resp.content[:4] != b"%PDF" and "pdf" not in content_type:
                return {
                    "success": False,
                    "path": "",
                    "size_bytes": 0,
                    "message": f"下载内容不是 PDF (content-type: {content_type})",
                }

            save_path.write_bytes(resp.content)

            return {
                "success": True,
                "path": str(save_path),
                "size_bytes": len(resp.content),
                "message": f"PDF 已保存到 {save_path}",
            }

        except httpx.HTTPError as e:
            return {
                "success": False,
                "path": "",
                "size_bytes": 0,
                "message": f"下载失败: {e}",
            }
