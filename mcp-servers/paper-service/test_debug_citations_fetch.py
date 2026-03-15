"""Targeted regression tests for citations/fetch debug fixes."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sources import semantic_scholar
from tools import fetch_paper as fetch_paper_tool
from tools import get_citations as get_citations_tool


class DummyMCP:
    """Minimal MCP stub used to capture registered tool callables."""

    def __init__(self) -> None:
        self.tools: dict[str, Callable[..., Any]] = {}

    def tool(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.tools[fn.__name__] = fn
            return fn

        return decorator


class FakeClient:
    """Queue-based async client for deterministic HTTP responses."""

    def __init__(self, responses: list[httpx.Response]) -> None:
        self._responses = list(responses)

    async def get(self, *args, **kwargs) -> httpx.Response:  # noqa: ANN002, ANN003
        if not self._responses:
            raise AssertionError("No fake responses left")
        return self._responses.pop(0)


def _response(
    status_code: int,
    *,
    json_data: dict | None = None,
    text: str = "",
) -> httpx.Response:
    request = httpx.Request("GET", "https://api.semanticscholar.org/mock")
    if json_data is not None:
        return httpx.Response(status_code, request=request, json=json_data)
    return httpx.Response(status_code, request=request, text=text)


@pytest.mark.asyncio
async def test_get_citations_invalid_direction_raises_value_error() -> None:
    mcp = DummyMCP()
    get_citations_tool.register(mcp)  # type: ignore[arg-type]
    get_citations = mcp.tools["get_citations"]

    with pytest.raises(ValueError, match="Invalid direction"):
        await get_citations(identifier="10.1000/test", direction="bad")  # type: ignore[misc]


@pytest.mark.asyncio
async def test_semantic_scholar_get_citations_references_429_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        semantic_scholar,
        "get_client",
        lambda: FakeClient([_response(429, text="rate limited")]),
    )

    with pytest.raises(httpx.HTTPStatusError):
        await semantic_scholar.get_citations.__wrapped__(  # type: ignore[attr-defined]
            "DOI:10.1000/test",
            direction="references",
            limit=5,
            api_key=None,
        )


@pytest.mark.asyncio
async def test_semantic_scholar_get_citations_citations_500_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        semantic_scholar,
        "get_client",
        lambda: FakeClient([_response(500, text="server error")]),
    )

    with pytest.raises(httpx.HTTPStatusError):
        await semantic_scholar.get_citations.__wrapped__(  # type: ignore[attr-defined]
            "DOI:10.1000/test",
            direction="citations",
            limit=5,
            api_key=None,
        )


@pytest.mark.asyncio
async def test_semantic_scholar_get_citations_both_200_returns_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    references = {
        "data": [
            {"citedPaper": {"paperId": "R1", "title": "Ref 1"}},
            {"citedPaper": {"paperId": "R2", "title": "Ref 2"}},
            {"citedPaper": None},
        ]
    }
    citations = {
        "data": [
            {"citingPaper": {"paperId": "C1", "title": "Cite 1"}},
            {"citingPaper": {"paperId": "C2", "title": "Cite 2"}},
            {"citingPaper": None},
        ]
    }
    monkeypatch.setattr(
        semantic_scholar,
        "get_client",
        lambda: FakeClient(
            [
                _response(200, json_data=references),
                _response(200, json_data=citations),
            ]
        ),
    )

    data = await semantic_scholar.get_citations.__wrapped__(  # type: ignore[attr-defined]
        "DOI:10.1000/test",
        direction="both",
        limit=5,
        api_key=None,
    )
    assert len(data["references"]) == 2
    assert len(data["citations"]) == 2
    assert data["references"][0]["paperId"] == "R1"
    assert data["citations"][0]["paperId"] == "C1"


@pytest.mark.asyncio
async def test_fetch_paper_uses_openalex_fallback_without_email(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mcp = DummyMCP()
    fetch_paper_tool.register(mcp)  # type: ignore[arg-type]
    fetch_paper = mcp.tools["fetch_paper"]

    monkeypatch.setattr(
        fetch_paper_tool,
        "_load_config",
        lambda: {
            "email": None,
            "shadow_library_enabled": False,
            "shadow_tls_mode": "strict_then_fallback",
        },
    )

    async def fake_openalex_get_by_doi(doi: str, *, email: str | None = None) -> dict:
        assert doi == "10.1000/test"
        assert email is None
        return {
            "title": "Sample Paper",
            "is_oa": False,
            "oa_url": None,
            "authors": ["A"],
        }

    async def fake_none(*args, **kwargs):  # noqa: ANN002, ANN003
        return None

    async def should_not_call_unpaywall(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("Unpaywall should not be called without email")

    monkeypatch.setattr(fetch_paper_tool.openalex, "get_by_doi", fake_openalex_get_by_doi)
    monkeypatch.setattr(fetch_paper_tool.core_api, "get_by_doi", fake_none)
    monkeypatch.setattr(fetch_paper_tool.europe_pmc, "get_by_doi", fake_none)
    monkeypatch.setattr(fetch_paper_tool.unpaywall, "find_oa", should_not_call_unpaywall)

    result = await fetch_paper(identifier="10.1000/test")  # type: ignore[misc]
    assert result["access_state"] == "abstract_only"
    assert result["access_source"] == "openalex_metadata"
    assert result["metadata"]["title"] == "Sample Paper"
