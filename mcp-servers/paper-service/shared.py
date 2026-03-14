"""共享基础设施：httpx 连接池 + 通用重试 + DOI 查询缓存"""

from __future__ import annotations

import asyncio
import functools
import logging
import time
from typing import Any, Callable

import httpx

logger = logging.getLogger("paper-service")

# ── httpx 连接池（模块级复用）──

_client: httpx.AsyncClient | None = None


def get_client(*, verify: bool = True) -> httpx.AsyncClient:
    """获取复用的 httpx 连接池。"""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            verify=verify,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _client


async def close_client() -> None:
    """关闭连接池（进程退出时调用）。"""
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None


# ── 通用重试装饰器 ──

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def with_retry(
    max_attempts: int = 3,
    backoff: list[float] | None = None,
    retry_on_status: set[int] | None = None,
):
    """通用 HTTP 重试装饰器（指数退避）。

    用法:
        @with_retry(max_attempts=3)
        async def my_api_call(...): ...
    """
    if backoff is None:
        backoff = [1.0, 3.0, 10.0]
    if retry_on_status is None:
        retry_on_status = RETRYABLE_STATUS

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code not in retry_on_status:
                        raise
                    last_exc = e
                    if attempt < max_attempts - 1:
                        wait = backoff[min(attempt, len(backoff) - 1)]
                        logger.warning(
                            f"[重试] {func.__name__} 第 {attempt + 1} 次失败 "
                            f"(HTTP {e.response.status_code})，{wait}s 后重试"
                        )
                        await asyncio.sleep(wait)
                    else:
                        logger.warning(
                            f"[重试] {func.__name__} 第 {attempt + 1} 次失败 "
                            f"(HTTP {e.response.status_code})，已达最大重试次数"
                        )
                except (httpx.ConnectError, httpx.ReadTimeout) as e:
                    last_exc = e
                    if attempt < max_attempts - 1:
                        wait = backoff[min(attempt, len(backoff) - 1)]
                        logger.warning(
                            f"[重试] {func.__name__} 第 {attempt + 1} 次失败 "
                            f"({type(e).__name__})，{wait}s 后重试"
                        )
                        await asyncio.sleep(wait)
                    else:
                        logger.warning(
                            f"[重试] {func.__name__} 第 {attempt + 1} 次失败 "
                            f"({type(e).__name__})，已达最大重试次数"
                        )
            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator


# ── DOI 查询缓存（会话级） ──

_doi_cache: dict[str, tuple[float, Any]] = {}
DOI_CACHE_TTL = 600  # 10 分钟


def cache_get(key: str) -> Any | None:
    """从缓存获取，过期返回 None。"""
    if key in _doi_cache:
        ts, value = _doi_cache[key]
        if time.time() - ts < DOI_CACHE_TTL:
            return value
        del _doi_cache[key]
    return None


def cache_set(key: str, value: Any) -> None:
    """写入缓存。"""
    _doi_cache[key] = (time.time(), value)


def cache_key(source: str, identifier: str) -> str:
    """生成缓存 key。"""
    return f"{source}:{identifier.lower().strip()}"
