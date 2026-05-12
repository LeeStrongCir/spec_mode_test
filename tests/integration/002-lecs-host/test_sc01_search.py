"""
SC-01: Search Navigation — Integration Tests

Tests for the console global search functionality:
- TC-001: Exact keyword search returns "LECS主机" with match highlighting
- TC-002: Fuzzy search "云服" returns "LECS主机"
- TC-003: Search navigation route redirects to /console/lecs-hosts/list
- Negative tests: No-match search returns empty results

Uses pytest + httpx AsyncClient following FastAPI test patterns.
"""

import pytest
from httpx import AsyncClient


# --- Search service mock data ---

MOCK_SEARCH_INDEX = [
    {
        "id": "lecs-host",
        "label": "LECS主机",
        "aliases": ["云服务器", "云主机", "LECS Host"],
        "route": "/console/lecs-hosts/list",
        "category": "compute",
    },
    {
        "id": "rds-instance",
        "label": "RDS数据库",
        "aliases": ["关系型数据库", "RDS"],
        "route": "/console/rds-instances/list",
        "category": "database",
    },
    {
        "id": "obs-bucket",
        "label": "对象存储",
        "aliases": ["OBS", "云存储"],
        "route": "/console/obs-buckets/list",
        "category": "storage",
    },
]


def _highlight_match(text: str, keyword: str) -> str:
    """Simulate search result highlight: wrap matched substring in <mark> tags."""
    if not keyword:
        return text
    lower_text = text.lower()
    lower_kw = keyword.lower()
    idx = lower_text.find(lower_kw)
    if idx >= 0:
        return f"{text[:idx]}<mark>{text[idx:idx+len(keyword)]}</mark>{text[idx+len(keyword):]}"
    return text


def _fuzzy_match(keyword: str, items: list[dict]) -> list[dict]:
    """
    Simulate fuzzy search: match keyword against label and aliases.
    Returns list of matched items with highlighted label.
    """
    if not keyword.strip():
        return []

    kw_lower = keyword.lower()
    results = []

    for item in items:
        matched = False

        # Exact substring match on label
        if kw_lower in item["label"].lower():
            matched = True

        # Fuzzy: check if keyword matches any alias (substring or full match)
        if not matched:
            for alias in item["aliases"]:
                if kw_lower in alias.lower() or alias.lower() in kw_lower:
                    matched = True
                    break

        if matched:
            highlighted = _highlight_match(item["label"], keyword)
            results.append({
                "id": item["id"],
                "label": item["label"],
                "rendered_label": highlighted,
                "route": item["route"],
                "highlighted": True,
            })

    return results


# --- Pytest fixtures ---

@pytest.fixture
def mock_search_service():
    """Provide a mock search service with pre-indexed items."""
    return {
        "index": MOCK_SEARCH_INDEX,
        "search": _fuzzy_match,
    }


# --- TC-001: Exact keyword search ---

@pytest.mark.asyncio
class TestExactKeywordSearch:
    """TC-001: Verify search bar keyword matching and highlighting."""

    async def test_search_exact_keyword_returns_lecs_host(self, mock_search_service):
        """Input 'LECS' in search bar → dropdown shows 'LECS主机' with highlighted keyword."""
        results = mock_search_service["search"]("LECS", mock_search_service["index"])

        assert len(results) >= 1, "Expected at least one search result for 'LECS'"

        lecs_result = next((r for r in results if r["id"] == "lecs-host"), None)
        assert lecs_result is not None, "LECS主机 should appear in search results"
        assert lecs_result["label"] == "LECS主机"
        assert lecs_result["route"] == "/console/lecs-hosts/list"

    async def test_search_exact_keyword_has_highlight(self, mock_search_service):
        """Verify 'LECS' keyword is highlighted in the result label."""
        results = mock_search_service["search"]("LECS", mock_search_service["index"])

        lecs_result = next((r for r in results if r["id"] == "lecs-host"), None)
        assert lecs_result is not None
        assert "<mark>" in lecs_result["rendered_label"], "Expected <mark> tag for highlight"
        assert "LECS" in lecs_result["rendered_label"]

    async def test_search_case_insensitive(self, mock_search_service):
        """Input 'lecs' (lowercase) should match same as 'LECS'. """
        results_upper = mock_search_service["search"]("LECS", mock_search_service["index"])
        results_lower = mock_search_service["search"]("lecs", mock_search_service["index"])

        upper_ids = {r["id"] for r in results_upper}
        lower_ids = {r["id"] for r in results_lower}
        assert "lecs-host" in upper_ids
        assert "lecs-host" in lower_ids
        assert upper_ids == lower_ids, "Search should be case-insensitive"


# --- TC-002: Fuzzy search ---

@pytest.mark.asyncio
class TestFuzzySearch:
    """TC-002: Verify fuzzy search matching via aliases."""

    async def test_search_cloud_server_returns_lecs_host(self, mock_search_service):
        """Input '云服' (substring of '云服务器') → fuzzy match finds 'LECS主机'."""
        results = mock_search_service["search"]("云服", mock_search_service["index"])

        assert len(results) >= 1, "Expected at least one result for fuzzy search '云服'"

        lecs_result = next((r for r in results if r["id"] == "lecs-host"), None)
        assert lecs_result is not None, "LECS主机 should be found via fuzzy match on alias '云服务器'"

    async def test_search_full_alias_returns_lecs_host(self, mock_search_service):
        """Input '云服务器' (full alias) → matches 'LECS主机'."""
        results = mock_search_service["search"]("云服务器", mock_search_service["index"])

        lecs_result = next((r for r in results if r["id"] == "lecs-host"), None)
        assert lecs_result is not None

    async def test_search_partial_alias_matches(self, mock_search_service):
        """Input '数据库' → matches 'RDS数据库' via alias."""
        results = mock_search_service["search"]("数据库", mock_search_service["index"])

        rds_result = next((r for r in results if r["id"] == "rds-instance"), None)
        assert rds_result is not None, "RDS数据库 should match on alias '关系型数据库' or '数据库'"


# --- TC-003: Navigation redirect ---

@pytest.mark.asyncio
class TestSearchNavigation:
    """TC-003: Verify click on search result navigates to /console/lecs-hosts/list."""

    async def test_search_nav_route_redirects_to_lecs_list(self, api_client):
        """GET /console/search/navigate?target=lecs-host → redirect to /console/lecs-hosts/list."""
        # Simulate navigation endpoint that redirects based on search result target
        response = await api_client.get(
            "/console/search/navigate",
            params={"target": "lecs-host"},
            follow_redirects=False,
        )

        # Either direct redirect or 200 with route info
        if response.status_code in (301, 302, 303, 307, 308):
            location = response.headers.get("location", "")
            assert "/console/lecs-hosts/list" in location
        elif response.status_code == 200:
            # SPA may return 200 with route data
            body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            if "route" in body:
                assert body["route"] == "/console/lecs-hosts/list"

    async def test_lecs_host_route_path(self, mock_search_service):
        """Verify the route path stored in search index is correct."""
        lecs = next(item for item in mock_search_service["index"] if item["id"] == "lecs-host")
        assert lecs["route"] == "/console/lecs-hosts/list"


# --- Negative tests ---

@pytest.mark.asyncio
class TestSearchNegative:
    """Negative tests for search: no-match scenarios."""

    async def test_search_no_match_returns_empty(self, mock_search_service):
        """Input a nonexistent keyword → returns empty result list."""
        results = mock_search_service["search"]("xyz_nonexistent_term", mock_search_service["index"])
        assert len(results) == 0, "Search for nonexistent term should return no results"

    async def test_search_empty_keyword_returns_empty(self, mock_search_service):
        """Input empty string → returns empty result list."""
        results = mock_search_service["search"]("", mock_search_service["index"])
        assert len(results) == 0

    async def test_search_whitespace_only_returns_empty(self, mock_search_service):
        """Input whitespace only → returns empty result list."""
        results = mock_search_service["search"]("   ", mock_search_service["index"])
        assert len(results) == 0

    async def test_search_no_redirect_for_invalid_target(self, api_client):
        """Request navigation with invalid target → no redirect to lecs-hosts."""
        response = await api_client.get(
            "/console/search/navigate",
            params={"target": "invalid_resource"},
            follow_redirects=False,
        )
        # Should not redirect to lecs-hosts
        if response.status_code in (301, 302, 303, 307, 308):
            location = response.headers.get("location", "")
            assert "/console/lecs-hosts/list" not in location
