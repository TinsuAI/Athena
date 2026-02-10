"""LLM-based reasoning service for HS code classification explanations."""

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
REASONING_CACHE_TTL = settings.llm_reasoning_cache_ttl


@dataclass
class ClassificationReasoning:
    """Result from LLM reasoning generation."""

    material: str
    function: str


# System prompt for classification reasoning
REASONING_SYSTEM_PROMPT = """Bạn là chuyên gia phân loại hải quan Việt Nam.
Nhiệm vụ: Giải thích lý do phân loại mã HS cho sản phẩm.

Quy tắc:
1. Giải thích ngắn gọn, chính xác, không mâu thuẫn
2. Nếu chức năng quyết định phân loại (không phải vật liệu), giải thích rõ tại sao
3. Tham chiếu Quy tắc tổng quát (GRI) khi cần thiết
4. Luôn nhất quán với mã HS đã cho - KHÔNG đề cập đến chương khác nếu mã HS thuộc chương hiện tại
5. Với sản phẩm kim loại mạ (chrome, nickel, etc.): nếu mã HS thuộc Chương 84 (máy móc), giải thích rằng chức năng quyết định phân loại, không phải vật liệu

Trả về JSON với định dạng chính xác:
{
  "material": "Giải thích về vật liệu và tại sao (không) ảnh hưởng phân loại",
  "function": "Giải thích chức năng và lý do phân loại vào nhóm này"
}"""

REASONING_USER_TEMPLATE = """Sản phẩm: {query}

Mã HS: {hs_code}
Chương: {chapter_info}
Nhóm: {heading_info}
Mô tả: {description}

Giải thích lý do phân loại."""


class LLMReasoningService:
    """Service for generating classification reasoning using LLM.

    Features:
    - Integrates with OpenRouter API for chat completions
    - Redis caching for repeated queries (24-hour TTL)
    - Retry logic with exponential backoff for API failures
    - Returns structured classification reasoning
    """

    def __init__(
        self,
        redis_client: redis.Redis | None = None,  # type: ignore[type-arg]
        model: str | None = None,
    ):
        """Initialize LLM reasoning service.

        Args:
            redis_client: Redis client for caching. If None, caching is disabled.
            model: LLM model to use. If None, uses default from settings.
        """
        self.redis_client = redis_client
        self.api_key = settings.openrouter_api_key
        self.model = model or settings.llm_reasoning_model
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay for exponential backoff (seconds)

    def _get_cache_key(self, query: str, hs_code: str) -> str:
        """Generate a cache key for the given query, HS code, and model.

        Uses MD5 hash to create a consistent, compact key.

        Args:
            query: The search query
            hs_code: The HS code string

        Returns:
            Cache key with 'reason:' prefix
        """
        combined = f"{query}:{hs_code}:{self.model}"
        text_hash = hashlib.md5(combined.encode("utf-8")).hexdigest()
        return f"reason:{text_hash}"

    async def _get_from_cache(self, query: str, hs_code: str) -> ClassificationReasoning | None:
        """Try to get reasoning from cache.

        Args:
            query: The search query
            hs_code: The HS code string

        Returns:
            Cached reasoning or None if not found
        """
        if not self.redis_client:
            return None

        try:
            cache_key = self._get_cache_key(query, hs_code)
            cached = await self.redis_client.get(cache_key)

            if cached:
                data = json.loads(cached)
                return ClassificationReasoning(
                    material=data["material"],
                    function=data["function"],
                )
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}")

        return None

    async def _save_to_cache(
        self,
        query: str,
        hs_code: str,
        reasoning: ClassificationReasoning,
    ) -> None:
        """Save reasoning to cache.

        Args:
            query: The search query
            hs_code: The HS code string
            reasoning: The reasoning to cache
        """
        if not self.redis_client:
            return

        try:
            cache_key = self._get_cache_key(query, hs_code)
            data = {
                "material": reasoning.material,
                "function": reasoning.function,
            }
            await self.redis_client.setex(
                cache_key,
                REASONING_CACHE_TTL,
                json.dumps(data, ensure_ascii=False),
            )
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")

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
            "X-Title": "Athena HS Code Lookup",
        }

        payload: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,  # Lower temperature for consistent reasoning
            "max_tokens": 800,  # Enough for Vietnamese reasoning text
        }

        # Only add response_format for models that support it (OpenAI models)
        if self.model.startswith("openai/"):
            payload["response_format"] = {"type": "json_object"}

        print(f"[LLM] Request to model={self.model}", flush=True)

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
        # Match ```json ... ``` or ``` ... ```
        code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
        if code_block_match:
            return json.loads(code_block_match.group(1))

        # Try finding JSON object in the content
        json_match = re.search(r"\{[\s\S]*\}", content)
        if json_match:
            return json.loads(json_match.group(0))

        raise json.JSONDecodeError(f"Could not find JSON in response", content, 0)

    async def _generate_with_retry(
        self,
        messages: list[dict[str, str]],
    ) -> ClassificationReasoning:
        """Generate reasoning with retry logic.

        Args:
            messages: Chat messages for the API

        Returns:
            ClassificationReasoning result

        Raises:
            Exception: If all retries fail
        """
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = await self._make_api_request(messages)

                print(f"[LLM] Response status: {response.status_code}", flush=True)

                if response.status_code == 200:
                    data = response.json()

                    # Log full response for debugging
                    print(f"[LLM] Response data: {json.dumps(data, ensure_ascii=False)[:500]}", flush=True)

                    # Check for API-level errors
                    if "error" in data:
                        error_msg = data["error"].get("message", str(data["error"]))
                        last_error = Exception(f"OpenRouter API error: {error_msg}")
                        logger.warning(f"LLM API error (attempt {attempt + 1}): {error_msg}")
                        continue

                    # Extract content from response
                    choices = data.get("choices", [])
                    if not choices:
                        last_error = Exception(f"No choices in API response: {data}")
                        logger.warning(f"LLM empty choices (attempt {attempt + 1}): {data}")
                        continue

                    content = choices[0].get("message", {}).get("content", "")
                    print(f"[LLM] Content: {content[:300] if content else '(empty)'}", flush=True)

                    # Parse JSON from content
                    parsed = self._extract_json_from_content(content)

                    return ClassificationReasoning(
                        material=parsed.get("material", ""),
                        function=parsed.get("function", ""),
                    )

                # Non-200 response, will retry
                response_text = response.text[:500] if response.text else "(empty)"
                last_error = Exception(
                    f"OpenRouter API error: {response.status_code} - {response_text}"
                )
                print(f"[LLM] API error (attempt {attempt + 1}): status={response.status_code}, body={response_text}", flush=True)

            except json.JSONDecodeError as e:
                last_error = Exception(f"Failed to parse LLM response: {e}")
                logger.warning(f"LLM parse error (attempt {attempt + 1}): {e}")

            except httpx.RequestError as e:
                last_error = e
                logger.warning(f"LLM request error (attempt {attempt + 1}): {e}")

            except KeyError as e:
                last_error = Exception(f"Unexpected response structure: missing {e}")
                logger.warning(f"LLM response structure error (attempt {attempt + 1}): {e}")

            # Exponential backoff before retry
            if attempt < self.max_retries - 1:
                delay = self.base_delay * (2**attempt)
                await asyncio.sleep(delay)

        raise Exception(
            f"Failed to generate reasoning after {self.max_retries} retries. "
            f"Last error: {last_error}"
        )

    async def generate_reasoning(
        self,
        query: str,
        hs_code: str,
        chapter_info: str,
        heading_info: str,
        description: str,
    ) -> ClassificationReasoning:
        """Generate classification reasoning for an HS code match.

        Features:
        - Checks cache first for repeated queries
        - Retries with exponential backoff on API failures
        - Caches successful results

        Args:
            query: The search query (product description)
            hs_code: The matched HS code (e.g., "8481.80.99")
            chapter_info: Chapter description (e.g., "Chương 84: Máy móc...")
            heading_info: Heading description (e.g., "Nhóm 84.81: Vòi, van...")
            description: HS code description

        Returns:
            ClassificationReasoning with material and function explanations

        Raises:
            Exception: If API fails after max retries
        """
        # Validate API key is available
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is required for LLM reasoning")

        # Normalize HS code for cache key (remove dots)
        hs_code_normalized = hs_code.replace(".", "")

        # Try cache first
        cached = await self._get_from_cache(query, hs_code_normalized)
        if cached:
            print(f"[LLM] Cache hit for: {query[:50]}...", flush=True)
            return cached

        print(f"[LLM] Cache miss, calling API for model={self.model}", flush=True)

        # Build user message from template
        user_message = REASONING_USER_TEMPLATE.format(
            query=query,
            hs_code=hs_code,
            chapter_info=chapter_info,
            heading_info=heading_info,
            description=description,
        )

        messages = [
            {"role": "system", "content": REASONING_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        # Generate with retries
        reasoning = await self._generate_with_retry(messages)

        # Cache the result
        await self._save_to_cache(query, hs_code_normalized, reasoning)

        return reasoning
