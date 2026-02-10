"""Query enhancement service for improving HS code search accuracy using LLM."""

import asyncio
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field

import httpx
import redis.asyncio as redis

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# OpenRouter API configuration
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"

# Cache TTL (default 24 hours)
ENHANCEMENT_CACHE_TTL = settings.llm_reasoning_cache_ttl


@dataclass
class EnhancedQuery:
    """Result from query enhancement."""

    original_query: str
    enhanced_query: str
    material_keywords: list[str] = field(default_factory=list)
    function_keywords: list[str] = field(default_factory=list)
    category: str = ""
    likely_chapters: list[str] = field(default_factory=list)


# System prompt for query enhancement
ENHANCEMENT_SYSTEM_PROMPT = """Bạn là chuyên gia phân tích sản phẩm cho phân loại hải quan.

Nhiệm vụ: Phân tích mô tả sản phẩm và trích xuất thông tin quan trọng để tìm kiếm mã HS.

## Hướng dẫn:
1. Xác định VẬT LIỆU chính (đồng, nhôm, thép, nhựa, cao su, gỗ, MDF, ván ép, v.v.)
2. Xác định CHỨC NĂNG/CÔNG DỤNG (dùng cho gì, dùng ở đâu)
3. Xác định DANH MỤC sản phẩm (đồ nội thất, phụ tùng xe, đồ điện, ĐỒ DÙNG NHÀ BẾP, v.v.)
4. Dự đoán các CHƯƠNG có thể áp dụng

## Một số chương thường gặp:
- Chương 39: Nhựa và sản phẩm nhựa
- Chương 40: Cao su và sản phẩm cao su
- Chương 44: GỖ và các sản phẩm gỗ (MDF, ván ép, đồ dùng nhà bếp bằng gỗ)
  - 4411: Ván sợi MDF/HDF THÔ (tấm nguyên liệu)
  - 4418: Cấu kiện xây dựng bằng gỗ (cửa, khung, sàn)
  - 4419: ĐỒ DÙNG NHÀ BẾP bằng gỗ (khay, thớt, đĩa, đũa - kể cả làm từ MDF)
  - 4420: Đồ gỗ khảm, hộp đựng đồ
- Chương 73: Sản phẩm bằng sắt thép
- Chương 74: Đồng và sản phẩm đồng
  - 7418.20: Đồ trang bị nhà vệ sinh bằng đồng (vòi, sen tắm, phụ kiện phòng tắm)
- Chương 76: Nhôm và sản phẩm nhôm
- Chương 83: Đồ kim loại trang trí, khóa, bản lề
- Chương 84: Máy móc, thiết bị cơ khí
- Chương 85: Thiết bị điện, điện tử
- Chương 87: Xe và phụ tùng xe
- Chương 94: Đồ nội thất lớn (bàn, ghế, tủ, giường)

## Nguyên tắc quan trọng:
- Sản phẩm hoàn chỉnh phân loại theo CHỨC NĂNG, không phải nguyên liệu
- Khay/đĩa/thớt bằng gỗ MDF → Chương 44 (đồ dùng nhà bếp), KHÔNG PHẢI Chương 94
- Tủ/bàn bằng gỗ MDF → Chương 94 (nội thất)

## Trong enhanced_query, BỔ SUNG:
- Loại sản phẩm cụ thể (khay, thớt, đĩa, đũa, v.v.)
- Từ khóa "đồ dùng nhà bếp bằng gỗ" nếu phù hợp
- Từ khóa "bộ đồ ăn" hoặc "bộ đồ làm bếp" nếu phù hợp

Trả về JSON với định dạng:
{
  "enhanced_query": "mô tả sản phẩm được làm rõ và bổ sung từ khóa quan trọng",
  "material_keywords": ["vật liệu 1", "vật liệu 2"],
  "function_keywords": ["chức năng 1", "chức năng 2"],
  "category": "danh mục sản phẩm",
  "likely_chapters": ["44", "94"]
}"""

ENHANCEMENT_USER_TEMPLATE = """Phân tích sản phẩm: {query}"""


class QueryEnhancementService:
    """Service for enhancing search queries using LLM analysis.

    Features:
    - Extracts material, function, and category from product descriptions
    - Redis caching for repeated queries (24-hour TTL)
    - Retry logic with exponential backoff for API failures
    - Graceful fallback to original query on failure
    """

    def __init__(
        self,
        redis_client: redis.Redis | None = None,  # type: ignore[type-arg]
        model: str | None = None,
    ):
        """Initialize query enhancement service.

        Args:
            redis_client: Redis client for caching. If None, caching is disabled.
            model: LLM model to use. If None, uses default from settings.
        """
        self.redis_client = redis_client
        self.api_key = settings.openrouter_api_key
        self.model = model or settings.llm_reasoning_model
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay for exponential backoff (seconds)

    def _get_cache_key(self, query: str) -> str:
        """Generate a cache key for the given query.

        Uses MD5 hash to create a consistent, compact key.

        Args:
            query: The search query

        Returns:
            Cache key with 'enhance:' prefix
        """
        combined = f"{query}:{self.model}"
        text_hash = hashlib.md5(combined.encode("utf-8")).hexdigest()
        return f"enhance:{text_hash}"

    async def _get_from_cache(self, query: str) -> EnhancedQuery | None:
        """Try to get enhanced query from cache.

        Args:
            query: The search query

        Returns:
            Cached result or None if not found
        """
        if not self.redis_client:
            return None

        try:
            cache_key = self._get_cache_key(query)
            cached = await self.redis_client.get(cache_key)

            if cached:
                data = json.loads(cached)
                return EnhancedQuery(
                    original_query=query,
                    enhanced_query=data.get("enhanced_query", query),
                    material_keywords=data.get("material_keywords", []),
                    function_keywords=data.get("function_keywords", []),
                    category=data.get("category", ""),
                    likely_chapters=data.get("likely_chapters", []),
                )
        except Exception as e:
            logger.warning(f"Enhance cache lookup failed: {e}")

        return None

    async def _save_to_cache(self, query: str, result: EnhancedQuery) -> None:
        """Save enhanced query to cache.

        Args:
            query: The original query
            result: The enhancement result to cache
        """
        if not self.redis_client:
            return

        try:
            cache_key = self._get_cache_key(query)
            data = {
                "enhanced_query": result.enhanced_query,
                "material_keywords": result.material_keywords,
                "function_keywords": result.function_keywords,
                "category": result.category,
                "likely_chapters": result.likely_chapters,
            }
            await self.redis_client.setex(
                cache_key,
                ENHANCEMENT_CACHE_TTL,
                json.dumps(data, ensure_ascii=False),
            )
        except Exception as e:
            logger.warning(f"Enhance cache save failed: {e}")

    async def _make_api_request(self, messages: list[dict[str, str]]) -> httpx.Response:
        """Make HTTP request to OpenRouter Chat API.

        Args:
            messages: List of chat messages

        Returns:
            HTTP response from OpenRouter
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://athena.example.com",
            "X-Title": "Athena Query Enhancement",
        }

        payload: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 400,
        }

        # Only add response_format for models that support it (OpenAI models)
        if self.model.startswith("openai/"):
            payload["response_format"] = {"type": "json_object"}

        print(f"[Enhance] Request to model={self.model}", flush=True)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                OPENROUTER_CHAT_URL,
                headers=headers,
                json=payload,
            )
            return response

    def _extract_json_from_content(self, content: str) -> dict:
        """Extract JSON from LLM response content.

        Handles cases where JSON is wrapped in markdown code blocks.

        Args:
            content: Raw content from LLM response

        Returns:
            Parsed JSON dict

        Raises:
            json.JSONDecodeError: If content cannot be parsed as JSON
        """
        if not content or not content.strip():
            raise json.JSONDecodeError("Empty response content", content or "", 0)

        content = content.strip()

        # Try direct JSON parse first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
        if code_block_match:
            return json.loads(code_block_match.group(1))

        # Try finding JSON object in the content
        json_match = re.search(r"\{[\s\S]*\}", content)
        if json_match:
            return json.loads(json_match.group(0))

        raise json.JSONDecodeError("Could not find JSON in response", content, 0)

    async def _enhance_with_retry(
        self,
        query: str,
        messages: list[dict[str, str]],
    ) -> EnhancedQuery:
        """Enhance query with retry logic.

        Args:
            query: Original query (for fallback)
            messages: Chat messages for the API

        Returns:
            EnhancedQuery result

        Raises:
            Exception: If all retries fail
        """
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = await self._make_api_request(messages)

                print(f"[Enhance] Response status: {response.status_code}", flush=True)

                if response.status_code == 200:
                    data = response.json()

                    # Check for API-level errors
                    if "error" in data:
                        error_msg = data["error"].get("message", str(data["error"]))
                        last_error = Exception(f"OpenRouter API error: {error_msg}")
                        logger.warning(f"Enhance API error (attempt {attempt + 1}): {error_msg}")
                        continue

                    # Extract content from response
                    choices = data.get("choices", [])
                    if not choices:
                        last_error = Exception(f"No choices in API response: {data}")
                        continue

                    content = choices[0].get("message", {}).get("content", "")
                    print(f"[Enhance] Content: {content[:200] if content else '(empty)'}", flush=True)

                    # Parse JSON from content
                    parsed = self._extract_json_from_content(content)

                    return EnhancedQuery(
                        original_query=query,
                        enhanced_query=parsed.get("enhanced_query", query),
                        material_keywords=parsed.get("material_keywords", []),
                        function_keywords=parsed.get("function_keywords", []),
                        category=parsed.get("category", ""),
                        likely_chapters=parsed.get("likely_chapters", []),
                    )

                # Non-200 response, will retry
                response_text = response.text[:500] if response.text else "(empty)"
                last_error = Exception(
                    f"OpenRouter API error: {response.status_code} - {response_text}"
                )
                print(f"[Enhance] API error (attempt {attempt + 1}): status={response.status_code}", flush=True)

            except json.JSONDecodeError as e:
                last_error = Exception(f"Failed to parse enhance response: {e}")
                logger.warning(f"Enhance parse error (attempt {attempt + 1}): {e}")

            except httpx.RequestError as e:
                last_error = e
                logger.warning(f"Enhance request error (attempt {attempt + 1}): {e}")

            # Exponential backoff before retry
            if attempt < self.max_retries - 1:
                delay = self.base_delay * (2**attempt)
                await asyncio.sleep(delay)

        raise Exception(
            f"Failed to enhance query after {self.max_retries} retries. "
            f"Last error: {last_error}"
        )

    async def enhance_query(self, query: str) -> EnhancedQuery:
        """Enhance a search query using LLM analysis.

        Extracts material, function, category, and likely chapters from the query
        to improve search accuracy.

        Args:
            query: The original search query (product description)

        Returns:
            EnhancedQuery with extracted information
        """
        # Return original if query is too short
        if len(query.strip()) < 3:
            return EnhancedQuery(
                original_query=query,
                enhanced_query=query,
            )

        # Validate API key is available
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not set, skipping query enhancement")
            return EnhancedQuery(
                original_query=query,
                enhanced_query=query,
            )

        # Try cache first
        cached = await self._get_from_cache(query)
        if cached:
            print(f"[Enhance] Cache hit for: {query[:50]}...", flush=True)
            return cached

        print(f"[Enhance] Cache miss, calling API", flush=True)

        # Build user message
        user_message = ENHANCEMENT_USER_TEMPLATE.format(query=query)

        messages = [
            {"role": "system", "content": ENHANCEMENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        try:
            # Enhance with retries
            result = await self._enhance_with_retry(query, messages)

            # Cache the result
            await self._save_to_cache(query, result)

            return result

        except Exception as e:
            logger.error(f"Query enhancement failed: {e}")
            # Graceful degradation: return original query unchanged
            return EnhancedQuery(
                original_query=query,
                enhanced_query=query,
            )
