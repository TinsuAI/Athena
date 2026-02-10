"""Reranking service for improving HS code search accuracy using LLM."""

import asyncio
import hashlib
import json
import logging
import re
from dataclasses import dataclass

import httpx
import redis.asyncio as redis

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# OpenRouter API configuration
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"

# Cache TTL (default 24 hours)
RERANKING_CACHE_TTL = settings.llm_reasoning_cache_ttl


@dataclass
class RerankResult:
    """Result from LLM reranking."""

    best_code: str
    reasoning: str


# System prompt for reranking candidates
RERANKING_SYSTEM_PROMPT = """Bạn là chuyên gia phân loại hải quan Việt Nam với kiến thức sâu về Quy tắc tổng quát (GRI).

Nhiệm vụ: Chọn mã HS phù hợp nhất cho sản phẩm từ danh sách ứng viên.

## NGUYÊN TẮC CỐT LÕI: SẢN PHẨM HOÀN CHỈNH vs. NGUYÊN LIỆU THÔ

**QUAN TRỌNG NHẤT:** Phân biệt giữa nguyên liệu thô và sản phẩm hoàn chỉnh:
- Nếu sản phẩm có CHỨC NĂNG CỤ THỂ (đồ dùng nhà bếp, nội thất, phụ kiện...) → phân loại theo CHỨC NĂNG
- Mã nguyên liệu thô (ván gỗ, tấm kim loại, sợi...) chỉ dùng cho vật liệu CHƯA GIA CÔNG thành sản phẩm

**Ví dụ quan trọng - Chương 44 (Gỗ):**
- 4411.xx = Ván sợi MDF/HDF THÔ (tấm, ván nguyên liệu chưa chế biến thành sản phẩm)
- 4419.xx = Đồ dùng nhà bếp/bàn bằng gỗ (sản phẩm hoàn chỉnh như khay, đĩa, thớt, đũa)
- → Khay chia bát đĩa làm từ MDF = 4419.xx (đồ dùng nhà bếp), KHÔNG PHẢI 4411.xx (ván MDF thô)
- → Thớt gỗ MDF = 4419.xx, KHÔNG PHẢI 4411.xx

**Ví dụ khác:**
- Tủ bếp MDF = 9403.xx (đồ nội thất), KHÔNG PHẢI 4411.xx
- Khung cửa MDF = 4418.xx (cấu kiện xây dựng), KHÔNG PHẢI 4411.xx
- Hộp đựng đồ MDF = 4420.xx (đồ gỗ khảm), KHÔNG PHẢI 4411.xx

## Quy tắc phân loại GRI:
1. GRI 1: Phân loại theo văn bản mô tả nhóm và Chú giải Phần/Chương
2. GRI 3(a): Nhóm mô tả cụ thể hơn được ưu tiên
3. GRI 3(b): Đặc tính cơ bản quyết định (thường là chức năng, không phải vật liệu)
4. GRI 6: Phân loại trong phân nhóm theo văn bản

## Nguyên tắc bổ sung:
- Sản phẩm dùng cho đồ nội thất → Chương 83 hoặc 94
- Phụ tùng xe → Chương 87 (chỉ khi thực sự dùng cho xe)
- Đồ dùng nhà bếp/phòng tắm bằng kim loại → Chương 73-76 hoặc 83
- Máy móc và bộ phận → Chương 84-85

Trả về JSON với định dạng:
{
  "best_code": "mã HS 8 chữ số",
  "reasoning": "Giải thích ngắn gọn lý do chọn mã này theo GRI"
}"""

RERANKING_USER_TEMPLATE = """Sản phẩm cần phân loại: {query}

Các mã HS ứng viên:
{candidates}

Chọn mã HS phù hợp nhất và giải thích."""


class RerankingService:
    """Service for reranking HS code search candidates using LLM.

    Features:
    - Integrates with OpenRouter API for chat completions
    - Redis caching for repeated queries (24-hour TTL)
    - Retry logic with exponential backoff for API failures
    - Uses GRI rules for accurate classification
    """

    def __init__(
        self,
        redis_client: redis.Redis | None = None,  # type: ignore[type-arg]
        model: str | None = None,
    ):
        """Initialize reranking service.

        Args:
            redis_client: Redis client for caching. If None, caching is disabled.
            model: LLM model to use. If None, uses default from settings.
        """
        self.redis_client = redis_client
        self.api_key = settings.openrouter_api_key
        self.model = model or settings.llm_reasoning_model
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay for exponential backoff (seconds)

    def _get_cache_key(self, query: str, candidate_codes: list[str]) -> str:
        """Generate a cache key for the given query and candidates.

        Uses MD5 hash to create a consistent, compact key.

        Args:
            query: The search query
            candidate_codes: List of HS codes to rerank

        Returns:
            Cache key with 'rerank:' prefix
        """
        sorted_codes = ",".join(sorted(candidate_codes))
        combined = f"{query}:{sorted_codes}:{self.model}"
        text_hash = hashlib.md5(combined.encode("utf-8")).hexdigest()
        return f"rerank:{text_hash}"

    async def _get_from_cache(
        self, query: str, candidate_codes: list[str]
    ) -> RerankResult | None:
        """Try to get reranking result from cache.

        Args:
            query: The search query
            candidate_codes: List of HS codes

        Returns:
            Cached result or None if not found
        """
        if not self.redis_client:
            return None

        try:
            cache_key = self._get_cache_key(query, candidate_codes)
            cached = await self.redis_client.get(cache_key)

            if cached:
                data = json.loads(cached)
                return RerankResult(
                    best_code=data["best_code"],
                    reasoning=data["reasoning"],
                )
        except Exception as e:
            logger.warning(f"Rerank cache lookup failed: {e}")

        return None

    async def _save_to_cache(
        self,
        query: str,
        candidate_codes: list[str],
        result: RerankResult,
    ) -> None:
        """Save reranking result to cache.

        Args:
            query: The search query
            candidate_codes: List of HS codes
            result: The reranking result to cache
        """
        if not self.redis_client:
            return

        try:
            cache_key = self._get_cache_key(query, candidate_codes)
            data = {
                "best_code": result.best_code,
                "reasoning": result.reasoning,
            }
            await self.redis_client.setex(
                cache_key,
                RERANKING_CACHE_TTL,
                json.dumps(data, ensure_ascii=False),
            )
        except Exception as e:
            logger.warning(f"Rerank cache save failed: {e}")

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
            "X-Title": "Athena HS Code Reranking",
        }

        payload: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,  # Very low temperature for consistent reranking
            "max_tokens": 600,  # Enough for Vietnamese reasoning text
        }

        # Only add response_format for models that support it (OpenAI models)
        if self.model.startswith("openai/"):
            payload["response_format"] = {"type": "json_object"}

        print(f"[Rerank] Request to model={self.model}", flush=True)

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

    async def _rerank_with_retry(
        self,
        messages: list[dict[str, str]],
        candidate_codes: list[str],
    ) -> RerankResult:
        """Rerank candidates with retry logic.

        Args:
            messages: Chat messages for the API
            candidate_codes: List of candidate codes (for fallback)

        Returns:
            RerankResult with best code and reasoning

        Raises:
            Exception: If all retries fail
        """
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = await self._make_api_request(messages)

                print(f"[Rerank] Response status: {response.status_code}", flush=True)

                if response.status_code == 200:
                    data = response.json()

                    # Log full response for debugging
                    print(f"[Rerank] Response data: {json.dumps(data, ensure_ascii=False)[:800]}", flush=True)

                    # Check for API-level errors
                    if "error" in data:
                        error_msg = data["error"].get("message", str(data["error"]))
                        last_error = Exception(f"OpenRouter API error: {error_msg}")
                        logger.warning(f"Rerank API error (attempt {attempt + 1}): {error_msg}")
                        continue

                    # Extract content from response
                    choices = data.get("choices", [])
                    if not choices:
                        last_error = Exception(f"No choices in API response: {data}")
                        continue

                    content = choices[0].get("message", {}).get("content", "")
                    print(f"[Rerank] Content: {content[:200] if content else '(empty)'}", flush=True)

                    # Parse JSON from content
                    parsed = self._extract_json_from_content(content)

                    best_code = parsed.get("best_code", "")
                    # Normalize code: remove dots if present
                    best_code = best_code.replace(".", "")

                    return RerankResult(
                        best_code=best_code,
                        reasoning=parsed.get("reasoning", ""),
                    )

                # Non-200 response, will retry
                response_text = response.text[:500] if response.text else "(empty)"
                last_error = Exception(
                    f"OpenRouter API error: {response.status_code} - {response_text}"
                )
                print(f"[Rerank] API error (attempt {attempt + 1}): status={response.status_code}", flush=True)

            except json.JSONDecodeError as e:
                last_error = Exception(f"Failed to parse rerank response: {e}")
                logger.warning(f"Rerank parse error (attempt {attempt + 1}): {e}")

            except httpx.RequestError as e:
                last_error = e
                logger.warning(f"Rerank request error (attempt {attempt + 1}): {e}")

            # Exponential backoff before retry
            if attempt < self.max_retries - 1:
                delay = self.base_delay * (2**attempt)
                await asyncio.sleep(delay)

        raise Exception(
            f"Failed to rerank after {self.max_retries} retries. "
            f"Last error: {last_error}"
        )

    async def rerank(
        self,
        query: str,
        candidates: list[dict],
        top_k: int = 1,
    ) -> RerankResult | None:
        """Rerank search candidates using LLM classification expertise.

        Args:
            query: The search query (product description)
            candidates: List of candidate results with hs_code, description_vn, etc.
            top_k: Number of top results to return (currently only 1 supported)

        Returns:
            RerankResult with best code and reasoning, or None on failure
        """
        if not candidates:
            return None

        # Validate API key is available
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not set, skipping reranking")
            return None

        # Extract codes for cache key
        candidate_codes = [c.get("hs_code", "") for c in candidates]

        # Try cache first
        cached = await self._get_from_cache(query, candidate_codes)
        if cached:
            print(f"[Rerank] Cache hit for: {query[:50]}...", flush=True)
            return cached

        print(f"[Rerank] Cache miss, calling API", flush=True)

        # Format candidates for the prompt
        candidates_text = ""
        for i, c in enumerate(candidates, 1):
            hs_code = c.get("hs_code", "")
            # Format code with dots for readability
            if len(hs_code) == 8:
                formatted_code = f"{hs_code[:4]}.{hs_code[4:6]}.{hs_code[6:]}"
            else:
                formatted_code = hs_code

            desc_vn = c.get("description_vn", "")
            chapter_info = c.get("chapter_info", "")
            heading_info = c.get("heading_info", "")

            candidates_text += f"{i}. {formatted_code}: {desc_vn}\n"
            if chapter_info:
                candidates_text += f"   Chương: {chapter_info}\n"
            if heading_info:
                candidates_text += f"   Nhóm: {heading_info}\n"

        # Build user message
        user_message = RERANKING_USER_TEMPLATE.format(
            query=query,
            candidates=candidates_text,
        )

        messages = [
            {"role": "system", "content": RERANKING_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        try:
            # Rerank with retries
            result = await self._rerank_with_retry(messages, candidate_codes)

            # Validate result - make sure best_code is in candidates
            if result.best_code not in candidate_codes:
                logger.warning(
                    f"Rerank returned invalid code {result.best_code}, "
                    f"falling back to first candidate"
                )
                # Fallback: return first candidate
                return RerankResult(
                    best_code=candidate_codes[0],
                    reasoning="Fallback: original search ranking",
                )

            # Cache the result
            await self._save_to_cache(query, candidate_codes, result)

            return result

        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            # Graceful degradation: return None to use original order
            return None
