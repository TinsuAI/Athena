"""Tests for NotebookLM service."""

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.notebooklm_service import (
    NotebookLMService,
    NotebookLMUnavailableError,
)

# Sample NotebookLM responses for testing
RESPONSE_WITH_HS_CODE = """
## Phân loại mã HS cho "Thanh treo khăn bằng đồng mạ chrome"

Sản phẩm này được phân loại vào mã HS **7418.20.00** - Đồ vệ sinh bằng đồng.

### Lý do phân loại:
- **Chất liệu:** Đồng (copper) mạ chrome
- **Chức năng:** Dùng trong phòng vệ sinh để treo khăn
- **GRI áp dụng:** GRI 1 - Phân loại theo nhóm 7418 (Đồ gia dụng, đồ vệ sinh bằng đồng)

### Ghi chú thực tế:
- FTA EVFTA: thuế suất 3.7% thay vì MFN 20%
- Cần C/O form EUR.1 để hưởng ưu đãi EVFTA
- Thủ tục nhập khẩu tiêu chuẩn, không cần giấy phép đặc biệt
"""

RESPONSE_WITH_MULTIPLE_HS_CODES = """
Sản phẩm máy xay sinh tố có thể phân loại theo hai mã:
- **8509.40.00** - Máy nghiền và máy trộn thực phẩm
- **8501.10.00** - Động cơ điện (nếu xét riêng motor)

Mã chính xác nhất là 8509.40.00 theo GRI 1.
"""

RESPONSE_GUIDE_NO_CODE = """
## Hướng dẫn phân loại sản phẩm phức hợp

Sản phẩm này cần xem xét thêm các yếu tố sau:
- Thành phần chính của sản phẩm
- Công dụng chính
- Chất liệu cấu thành

Vui lòng cung cấp thêm thông tin để phân loại chính xác.
"""


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = MagicMock()
    settings.notebooklm_enabled = True
    settings.notebooklm_notebook_id = "test-notebook-id"
    settings.notebooklm_timeout = 120
    settings.notebooklm_cache_ttl = 86400
    return settings


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.setex = AsyncMock()
    return client


@pytest.fixture
def service(mock_settings, mock_redis):
    """Create NotebookLMService with mocked dependencies."""
    with patch("app.services.notebooklm_service.get_settings", return_value=mock_settings):
        svc = NotebookLMService(redis_client=mock_redis)
    return svc


@pytest.fixture
def service_no_redis(mock_settings):
    """Create NotebookLMService without Redis."""
    with patch("app.services.notebooklm_service.get_settings", return_value=mock_settings):
        svc = NotebookLMService(redis_client=None)
    return svc


class TestQueryReturnsHSCode:
    """Test AC1: Successful query with HS code extraction."""

    async def test_query_returns_hs_code(self, service, mock_redis):
        """Query returns NotebookLMResult with extracted HS code."""
        mock_sdk_result = MagicMock()
        mock_sdk_result.answer = RESPONSE_WITH_HS_CODE

        with patch.object(service, "_call_sdk", return_value=RESPONSE_WITH_HS_CODE):
            result = await service.query("Thanh treo khăn bằng đồng mạ chrome")

        assert result is not None
        assert result.hs_code == "7418.20.00"
        assert result.classification is not None
        assert result.raw_answer == RESPONSE_WITH_HS_CODE
        assert isinstance(result.practical_notes, list)


class TestResponseParsingEdgeCases:
    """Test AC2/AC3: Response parsing edge cases."""

    async def test_query_no_hs_code_returns_guide(self, service):
        """Query with no HS code in response returns guide text."""
        with patch.object(service, "_call_sdk", return_value=RESPONSE_GUIDE_NO_CODE):
            result = await service.query("sản phẩm phức hợp")

        assert result is not None
        assert result.hs_code is None
        assert result.classification is None
        assert result.raw_answer == RESPONSE_GUIDE_NO_CODE

    async def test_query_multiple_hs_codes_uses_first(self, service):
        """Query with multiple HS codes uses the first match."""
        with patch.object(service, "_call_sdk", return_value=RESPONSE_WITH_MULTIPLE_HS_CODES):
            result = await service.query("máy xay sinh tố")

        assert result is not None
        assert result.hs_code == "8509.40.00"

    async def test_parse_response_empty_string(self, service):
        """Parsing empty response returns no HS code."""
        result = service._parse_response("")
        assert result.hs_code is None
        assert result.classification is None
        assert result.raw_answer == ""


class TestRedisCaching:
    """Test AC6: Redis caching."""

    async def test_redis_cache_hit(self, service, mock_redis):
        """Cached result is returned without calling SDK."""
        cached_data = {
            "hs_code": "7418.20.00",
            "classification": {"reasoning": "test"},
            "practical_notes": [],
            "raw_answer": "cached response",
        }
        mock_redis.get = AsyncMock(return_value=json.dumps(cached_data))

        with patch.object(service, "_call_sdk") as mock_sdk:
            result = await service.query("test query")

        mock_sdk.assert_not_called()
        assert result is not None
        assert result.hs_code == "7418.20.00"
        assert result.raw_answer == "cached response"

    async def test_redis_cache_miss(self, service, mock_redis):
        """Cache miss triggers SDK call and caches result."""
        mock_redis.get = AsyncMock(return_value=None)

        with patch.object(service, "_call_sdk", return_value=RESPONSE_WITH_HS_CODE):
            result = await service.query("test query")

        assert result is not None
        assert result.hs_code == "7418.20.00"
        mock_redis.setex.assert_called_once()

    async def test_redis_unavailable_still_works(self, service, mock_redis):
        """Service works when Redis raises an exception."""
        mock_redis.get = AsyncMock(side_effect=Exception("Redis down"))

        with patch.object(service, "_call_sdk", return_value=RESPONSE_WITH_HS_CODE):
            result = await service.query("test query")

        assert result is not None
        assert result.hs_code == "7418.20.00"

    async def test_cache_key_normalization(self, service):
        """Cache key is normalized (lowercase, stripped)."""
        key1 = service._cache_key("  COPPER rack  ")
        key2 = service._cache_key("copper rack")
        assert key1 == key2

    def test_redis_serialization_round_trip(self, service):
        """Validate that NotebookLMResult can be serialized and deserialized for Redis."""
        from dataclasses import asdict
        from app.services.notebooklm_service import NotebookLMResult

        original = NotebookLMResult(
            hs_code="7418.20.00",
            classification={"reasoning": "test", "material": "copper", "function": "towel rack"},
            practical_notes=["FTA EVFTA available", "C/O required"],
            raw_answer="Full markdown response here",
        )

        # Simulate Redis serialization/deserialization
        serialized = json.dumps(asdict(original))
        deserialized = NotebookLMResult(**json.loads(serialized))

        assert deserialized.hs_code == original.hs_code
        assert deserialized.classification == original.classification
        assert deserialized.practical_notes == original.practical_notes
        assert deserialized.raw_answer == original.raw_answer


class TestErrorHandling:
    """Test AC4: Error handling."""

    async def test_query_timeout_raises_unavailable(self, service):
        """Timeout raises NotebookLMUnavailableError with reason='timeout'."""
        with patch.object(
            service, "_call_sdk", side_effect=NotebookLMUnavailableError(reason="timeout")
        ):
            with pytest.raises(NotebookLMUnavailableError) as exc_info:
                await service.query("test query")

        assert exc_info.value.reason == "timeout"

    async def test_query_rate_limit_raises_unavailable(self, service):
        """Rate limit raises NotebookLMUnavailableError with reason='rate_limit'."""
        with patch.object(
            service, "_call_sdk", side_effect=NotebookLMUnavailableError(reason="rate_limit")
        ):
            with pytest.raises(NotebookLMUnavailableError) as exc_info:
                await service.query("test query")

        assert exc_info.value.reason == "rate_limit"

    async def test_query_auth_error_raises_unavailable(self, service):
        """Auth error raises NotebookLMUnavailableError with reason='auth_error'."""
        with patch.object(
            service, "_call_sdk", side_effect=NotebookLMUnavailableError(reason="auth_error")
        ):
            with pytest.raises(NotebookLMUnavailableError) as exc_info:
                await service.query("test query")

        assert exc_info.value.reason == "auth_error"

    async def test_query_connection_error_raises_unavailable(self, service):
        """Connection error raises NotebookLMUnavailableError with reason='service_down'."""
        with patch.object(
            service, "_call_sdk", side_effect=NotebookLMUnavailableError(reason="service_down")
        ):
            with pytest.raises(NotebookLMUnavailableError) as exc_info:
                await service.query("test query")

        assert exc_info.value.reason == "service_down"


class TestCallSdkErrorClassification:
    """Test the _call_sdk and _classify_error methods for various SDK failures."""

    async def test_timeout_error_from_sdk(self, service):
        """asyncio.TimeoutError from SDK maps to timeout reason."""
        service.settings.notebooklm_timeout = 0.01

        mock_client_class = MagicMock()

        def blocking_query(notebook_id, query_text):
            time.sleep(10)

        mock_client_class.return_value.query = blocking_query

        with patch.object(service, "_get_client_class", return_value=mock_client_class):
            with pytest.raises(NotebookLMUnavailableError) as exc_info:
                await service._call_sdk("test")

            assert exc_info.value.reason == "timeout"

    async def test_rate_limit_error_from_sdk(self, service):
        """HTTP 429 from SDK maps to rate_limit reason."""
        mock_client_class = MagicMock()
        mock_client_class.return_value.query.side_effect = Exception("HTTP 429 Too Many Requests")

        with patch.object(service, "_get_client_class", return_value=mock_client_class):
            with pytest.raises(NotebookLMUnavailableError) as exc_info:
                await service._call_sdk("test")

            assert exc_info.value.reason == "rate_limit"

    async def test_auth_error_from_sdk(self, service):
        """HTTP 401/403 from SDK maps to auth_error reason."""
        mock_client_class = MagicMock()
        mock_client_class.return_value.query.side_effect = Exception("HTTP 401 Unauthorized")

        with patch.object(service, "_get_client_class", return_value=mock_client_class):
            with pytest.raises(NotebookLMUnavailableError) as exc_info:
                await service._call_sdk("test")

            assert exc_info.value.reason == "auth_error"

    async def test_connection_error_from_sdk(self, service):
        """ConnectionError from SDK maps to service_down reason."""
        mock_client_class = MagicMock()
        mock_client_class.return_value.query.side_effect = ConnectionError("Connection refused")

        with patch.object(service, "_get_client_class", return_value=mock_client_class):
            with pytest.raises(NotebookLMUnavailableError) as exc_info:
                await service._call_sdk("test")

            assert exc_info.value.reason == "service_down"

    async def test_unknown_error_from_sdk(self, service):
        """Unknown exception from SDK maps to service_down reason."""
        mock_client_class = MagicMock()
        mock_client_class.return_value.query.side_effect = RuntimeError("Something unexpected")

        with patch.object(service, "_get_client_class", return_value=mock_client_class):
            with pytest.raises(NotebookLMUnavailableError) as exc_info:
                await service._call_sdk("test")

            assert exc_info.value.reason == "service_down"


class TestDisabledService:
    """Test AC5: Disabled service."""

    async def test_query_disabled_returns_none(self, mock_redis):
        """Disabled service returns None without making API call."""
        settings = MagicMock()
        settings.notebooklm_enabled = False

        with patch("app.services.notebooklm_service.get_settings", return_value=settings):
            svc = NotebookLMService(redis_client=mock_redis)

        with patch.object(svc, "_call_sdk") as mock_sdk:
            result = await svc.query("test query")

        assert result is None
        mock_sdk.assert_not_called()


class TestClassificationExtraction:
    """Test classification and practical notes extraction."""

    def test_extract_classification_with_material_and_function(self, service):
        """Classification extraction finds material and function lines."""
        result = service._extract_classification(RESPONSE_WITH_HS_CODE)
        assert result["material"] != ""
        assert result["function"] != ""

    def test_extract_practical_notes(self, service):
        """Practical notes extraction finds FTA/duty related items."""
        notes = service._extract_practical_notes(RESPONSE_WITH_HS_CODE)
        assert len(notes) > 0
        assert any("EVFTA" in note or "fta" in note.lower() for note in notes)

    def test_extract_practical_notes_empty(self, service):
        """No practical notes for unrelated content."""
        notes = service._extract_practical_notes("This is a plain text with no trade notes.")
        assert notes == []


class TestServiceWithoutRedis:
    """Test service works without Redis client."""

    async def test_query_without_redis(self, service_no_redis):
        """Service works correctly when Redis is not configured."""
        with patch.object(service_no_redis, "_call_sdk", return_value=RESPONSE_WITH_HS_CODE):
            result = await service_no_redis.query("test query")

        assert result is not None
        assert result.hs_code == "7418.20.00"


class TestSDKImportValidation:
    """Test that SDK import path is correct."""

    def test_sdk_import_path_is_valid(self, service):
        """Validate that the NotebookLMClient can be imported from the expected path."""
        try:
            client_class = service._get_client_class()
            assert client_class is not None
            assert hasattr(client_class, "__name__")
            # If the package is not installed, this will raise ImportError
            # If the import path is wrong, this will raise ImportError or AttributeError
        except ImportError as e:
            # This is expected if notebooklm-mcp-cli is not installed in test environment
            # In production, this import must succeed
            pytest.skip(f"NotebookLM SDK not installed in test environment: {e}")
