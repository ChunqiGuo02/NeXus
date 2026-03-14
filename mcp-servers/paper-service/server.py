"""ARIA paper-service MCP Server 主入口

提供学术论文搜索、获取、验证、引用关系查询等工具。
10 个数据源，五级瀑布流获取策略。
"""

import atexit
import asyncio
import json
from pathlib import Path

from fastmcp import FastMCP
from shared import close_client
from tools.download_pdf import register as register_download
from tools.fetch_paper import register as register_fetch
from tools.get_citations import register as register_citations
from tools.search_papers import register as register_search
from tools.verify_citation import register as register_verify

mcp = FastMCP(
    "paper-service",
    instructions="学术论文搜索、获取、验证 MCP Server",
)

# 全局配置路径
GLOBAL_CONFIG_PATH = Path.home() / ".aria" / "global_config.json"


def load_config() -> dict:
    """加载全局配置，不存在则返回默认值。"""
    if GLOBAL_CONFIG_PATH.exists():
        return json.loads(GLOBAL_CONFIG_PATH.read_text(encoding="utf-8"))
    return {
        "setup_completed": False,
        "email": None,
        "semantic_scholar_key": None,
        "shadow_library_enabled": True,
        "shadow_sources": ["sci-hub", "libgen"],
        "shadow_tls_mode": "strict_then_fallback",
        "pdf_parser": "marker",
        "search_sources": ["semantic_scholar", "arxiv", "crossref", "openalex"],
        "max_concurrent_downloads": 3,
    }


def save_config(config: dict) -> None:
    """保存全局配置。"""
    GLOBAL_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    GLOBAL_CONFIG_PATH.write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ------ 注册 Tools ------

register_search(mcp)
register_fetch(mcp)
register_verify(mcp)
register_citations(mcp)
register_download(mcp)

# ------ 进程退出时关闭连接池 ------
def _cleanup():
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(close_client())
        loop.close()
    except Exception:
        pass  # 进程退出时连接池会随进程回收


atexit.register(_cleanup)

if __name__ == "__main__":
    mcp.run()
