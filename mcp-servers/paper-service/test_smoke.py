"""Phase 1 Smoke Test -- 验证核心功能 + 修复后回归测试"""

import asyncio
import importlib
import sys

import httpx
import pytest

sys.path.insert(0, ".")
pytestmark = pytest.mark.asyncio


def _skip(reason: str) -> dict[str, str | bool]:
    print(f"[SKIP] {reason}")
    return {"skipped": True, "reason": reason}


async def test_semantic_scholar():
    from sources import semantic_scholar

    try:
        results = await semantic_scholar.search("attention mechanism", limit=3)
    except httpx.HTTPStatusError as e:
        if e.response is not None and e.response.status_code == 429:
            return _skip("Semantic Scholar rate-limited (HTTP 429)")
        raise
    except httpx.ConnectError as e:
        return _skip(f"Semantic Scholar unreachable: {e}")

    print(f"[Semantic Scholar] Found {len(results)} papers")
    for p in results:
        title = p.get("title", "")[:60]
        print(f"  - {title}... ({p.get('year')})")
    assert len(results) > 0, "No results from Semantic Scholar"
    return True


async def test_arxiv():
    from sources import arxiv_source
    try:
        results = await arxiv_source.search("attention mechanism", limit=3)
    except httpx.ConnectError as e:
        return _skip(f"arXiv unreachable: {e}")
    print(f"[arXiv] Found {len(results)} papers")
    for p in results:
        title = p.get("title", "")[:60]
        print(f"  - {title}... ({p.get('year')})")
    assert len(results) > 0, "No results from arXiv"
    return True


async def test_crossref():
    from sources import crossref
    try:
        result = await crossref.get_by_doi("10.1038/nature12373")
    except httpx.ConnectError as e:
        return _skip(f"CrossRef unreachable: {e}")
    print(f"[CrossRef] DOI lookup: {result.get('title', 'FAILED')[:60]}")
    assert result is not None, "CrossRef DOI lookup failed"
    return True


async def test_openalex():
    from sources import openalex
    try:
        result = await openalex.get_by_doi("10.1038/nature12373")
    except httpx.ConnectError as e:
        return _skip(f"OpenAlex unreachable: {e}")
    print(f"[OpenAlex] DOI lookup: {result.get('title', 'FAILED')[:60]}")
    print(f"  is_retracted: {result.get('is_retracted')}")
    print(f"  cited_by_count: {result.get('cited_by_count')}")
    assert result is not None, "OpenAlex DOI lookup failed"
    return True


async def test_server_import():
    """P0: server.py 可以正常 import"""
    importlib.import_module("server")
    print("[Server] import OK, tools registered")
    return True


async def test_download_path_traversal():
    """P0: download_pdf 路径穿越防护"""
    from tools.download_pdf import _sanitize_filename
    
    # 合法文件名
    assert _sanitize_filename("paper.pdf") == "paper.pdf"
    assert _sanitize_filename("my_paper_2024.pdf") == "my_paper_2024.pdf"
    
    # 非法文件名
    assert _sanitize_filename("../evil.pdf") is None
    assert _sanitize_filename("..\\evil.pdf") is None
    assert _sanitize_filename("/etc/passwd") is None
    assert _sanitize_filename("C:\\Windows\\System32\\evil.pdf") is None
    assert _sanitize_filename("subdir/file.pdf") is None
    assert _sanitize_filename("") is None
    
    print("[Security] Path traversal protection: ALL PASSED")
    return True


async def test_verify_citation_real():
    """P1: 调用真实 verify_citation 实现，验证 2 源 = verified, 逻辑正确"""
    sys.path.insert(0, ".")
    from tools.verify_citation import (
        _title_match,
        _authors_overlap,
        _evaluate_status,
    )

    # 标题匹配测试
    assert _title_match("Attention Is All You Need", "attention is all you need")
    assert not _title_match("Attention Is All You Need", "BERT: Pre-training")

    # 作者匹配测试
    assert _authors_overlap(["Vaswani", "Shazeer"], ["Ashish Vaswani"])
    assert not _authors_overlap(["Smith", "Jones"], ["Vaswani"])

    # 状态判定主逻辑（纯函数）矩阵测试
    assert _evaluate_status(
        is_retracted=False,
        sources_confirmed=0,
        sources_checked=3,
        has_discrepancies=False,
    ) == ("unverified", 0.0)
    assert _evaluate_status(
        is_retracted=False,
        sources_confirmed=1,
        sources_checked=3,
        has_discrepancies=False,
    ) == ("unverified", 0.5)
    assert _evaluate_status(
        is_retracted=False,
        sources_confirmed=2,
        sources_checked=3,
        has_discrepancies=False,
    ) == ("verified", 0.67)

    # 真实 DOI 验证（调用 API）
    from sources import crossref, openalex
    try:
        cr = await crossref.get_by_doi("10.1038/nature12373")
        oa = await openalex.get_by_doi("10.1038/nature12373")
    except httpx.ConnectError as e:
        return _skip(f"Verify API dependency unreachable: {e}")

    sources_confirmed = 0
    if cr:
        sources_confirmed += 1
    if oa:
        sources_confirmed += 1

    # 至少两源才 verified（调用真实主逻辑函数）
    status, confidence = _evaluate_status(
        is_retracted=False,
        sources_confirmed=sources_confirmed,
        sources_checked=max(sources_confirmed, 1),
        has_discrepancies=False,
    )
    print(f"[Verify Real] {sources_confirmed} sources -> status={status}, confidence={confidence}")
    print("  title_match: OK, authors_overlap: OK")
    assert sources_confirmed >= 2
    assert status == "verified"
    return True


async def main():
    print("=" * 60)
    print("Phase 1 Smoke Test + Regression")
    print("=" * 60)

    tests = [
        ("Server Import", test_server_import),
        ("Path Traversal", test_download_path_traversal),
        ("Semantic Scholar", test_semantic_scholar),
        ("arXiv", test_arxiv),
        ("CrossRef", test_crossref),
        ("OpenAlex", test_openalex),
        ("Verify Real", test_verify_citation_real),
    ]

    passed = 0
    failed = 0
    skipped = 0
    for name, test_fn in tests:
        try:
            result = await test_fn()
            if isinstance(result, dict) and result.get("skipped"):
                skipped += 1
                reason = result.get("reason", "no reason provided")
                print(f"  >> {name} SKIPPED: {reason}\n")
                continue
            passed += 1
            print(f"  >> {name} PASSED\n")
        except Exception as e:
            failed += 1
            print(f"  >> {name} FAILED: {e}\n")

    print("=" * 60)
    print(f"Results: {passed} passed, {skipped} skipped, {failed} failed")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
