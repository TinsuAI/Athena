"""Integration tests for search API endpoint.

These tests require:
1. Running database with HS codes and embeddings populated
2. Running Redis instance
3. Valid OPENROUTER_API_KEY in environment

Run with: pytest app/api/search_integration_test.py -v --integration
"""

import pytest
import time
from httpx import AsyncClient

from app.main import app

# Skip all tests if --integration flag not provided
pytestmark = pytest.mark.skipif(
    "not config.getoption('--integration')",
    reason="Integration tests require --integration flag"
)


class TestVietnameseSearch:
    """AC1: Vietnamese Product Description Search"""

    @pytest.mark.asyncio
    async def test_detailed_vietnamese_description(self):
        """Test search with detailed Vietnamese customs declaration."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            start_time = time.time()

            response = await client.post(
                "/api/search",
                json={
                    "query": "Thanh treo khăn MITO, mã A2018ANE, bằng đồng mạ chrome, kích thước 33,5x8cm, nhà sản xuất INDA S.p.a, hàng mới 100%"
                }
            )

            elapsed = time.time() - start_time

            assert response.status_code == 200
            data = response.json()

            # AC1: Response includes required fields
            assert data["success"] is True
            assert "hs_code" in data["data"]
            assert "description" in data["data"]
            assert "duty_rate" in data["data"]
            assert "vat_rate" in data["data"]
            assert "classification" in data["data"]
            assert "material" in data["data"]["classification"]
            assert "function" in data["data"]["classification"]
            assert "practical_notes" in data["data"]
            assert "confidence" in data["data"]

            # NFR-P1: Response time <3 seconds
            assert elapsed < 3.0, f"Response time {elapsed:.2f}s exceeds 3s limit"


class TestSimpleVietnameseSearch:
    """AC2: Simple Vietnamese Description Search"""

    @pytest.mark.asyncio
    async def test_simple_vietnamese_query(self):
        """Test search with simple Vietnamese description."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/search",
                json={"query": "máy xay sinh tố"}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            # System extracts key features
            assert data["data"]["classification"]["material"]
            assert data["data"]["classification"]["function"]


class TestEnglishSearch:
    """AC3: English Description Search"""

    @pytest.mark.asyncio
    async def test_english_description(self):
        """Test search with English description."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/search",
                json={"query": "copper bathroom towel rack, chrome plated, 33.5x8cm"}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            # Reasoning should be in Vietnamese (per NFR-I3)
            classification = data["data"]["classification"]
            # Check for Vietnamese characters in reasoning
            assert any(
                ord(c) > 127
                for c in classification["material"] + classification["function"]
            ), "Classification reasoning should be in Vietnamese"


class TestChineseSearch:
    """AC4: Chinese Description Search (Best Effort)"""

    @pytest.mark.asyncio
    async def test_chinese_description_best_effort(self):
        """Test search with Chinese description returns best-effort result."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/search",
                json={"query": "铜制浴室毛巾架，镀铬"}
            )

            # Should return a result (best effort) or graceful no-result
            assert response.status_code in [200, 404]
            data = response.json()

            if data["success"]:
                # Best effort result found
                assert "hs_code" in data["data"]
            else:
                # No result is acceptable for Chinese (best effort)
                assert "No matching HS code found" in data["error"]["detail"]


class TestExactHSCodeSearch:
    """AC5: Exact HS Code Search"""

    @pytest.mark.asyncio
    async def test_exact_code_with_periods(self):
        """Test exact HS code lookup with periods."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/search",
                json={"query": "7418.20.00"}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["data"]["hs_code"] == "7418.20.00"
            # FR4: Exact match should be 100% confidence
            assert data["data"]["confidence"] == 100

    @pytest.mark.asyncio
    async def test_exact_code_without_periods(self):
        """Test exact HS code lookup without periods."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/search",
                json={"query": "74182000"}
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["data"]["hs_code"] == "7418.20.00"
            assert data["data"]["confidence"] == 100


class TestNoResultsHandling:
    """AC6: No Results Handling"""

    @pytest.mark.asyncio
    async def test_no_results_with_guidance(self):
        """Test search with no matches returns guidance."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/search",
                json={"query": "xyznonexistent123"}
            )

            assert response.status_code == 200 or response.status_code == 404
            data = response.json()

            assert data["success"] is False
            assert "error" in data
            assert "No matching HS code found" in data["error"]["detail"]
            assert "material" in data["error"]["detail"].lower() or \
                   "function" in data["error"]["detail"].lower()


class TestPerformance:
    """NFR-P1: Performance requirements"""

    @pytest.mark.asyncio
    async def test_response_time_under_3_seconds(self):
        """Verify response time <3 seconds for typical queries."""
        queries = [
            "máy xay sinh tố",
            "copper towel rack",
            "thanh treo khăn đồng",
            "7418.20.00",
        ]

        async with AsyncClient(app=app, base_url="http://test") as client:
            for query in queries:
                start_time = time.time()
                response = await client.post(
                    "/api/search",
                    json={"query": query}
                )
                elapsed = time.time() - start_time

                assert response.status_code in [200, 404]
                assert elapsed < 3.0, f"Query '{query}' took {elapsed:.2f}s"


class TestEdgeCases:
    """Document edge cases and limitations"""

    @pytest.mark.asyncio
    async def test_very_long_query(self):
        """Test handling of very long queries."""
        long_query = "máy " * 100  # Very long query
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/search",
                json={"query": long_query[:500]}  # Schema limits to 500 chars
            )
            # Should handle gracefully
            assert response.status_code in [200, 400, 404]

    @pytest.mark.asyncio
    async def test_special_characters(self):
        """Test handling of special characters in query."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/search",
                json={"query": "máy xay (gia đình) - 100W"}
            )
            assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_mixed_language_query(self):
        """Test handling of mixed language query."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/search",
                json={"query": "copper thanh treo khăn bathroom"}
            )
            assert response.status_code in [200, 404]
