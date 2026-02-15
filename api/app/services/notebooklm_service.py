"""NotebookLM service for HS code classification via Google NotebookLM."""

import asyncio
import hashlib
import json
import re
from dataclasses import asdict, dataclass

import redis.asyncio as redis

from app.core.config import get_settings

# HS code pattern: XXXX.XX.XX
HS_CODE_PATTERN = re.compile(r"\d{4}\.\d{2}\.\d{2}")


class NotebookLMUnavailableError(Exception):
    """Raised when NotebookLM service is unavailable."""

    def __init__(self, reason: str):
        self.reason = reason  # "timeout" | "rate_limit" | "auth_error" | "service_down"
        super().__init__(f"NotebookLM unavailable: {reason}")


@dataclass
class NotebookLMResult:
    """Result from NotebookLM query."""

    hs_code: str | None  # "7418.20.00" or None if guide/no-match
    classification: dict | None  # {"reasoning": "...", "material": "...", "function": "..."}
    practical_notes: list[str]  # Extracted practical guidance
    raw_answer: str  # Full NotebookLM markdown response


class NotebookLMService:
    """Service for querying NotebookLM for HS code classification.

    Wraps the NotebookLMClient SDK, parses responses to extract HS codes,
    and caches results in Redis.
    """

    def __init__(self, redis_client: redis.Redis | None = None):  # type: ignore[type-arg]
        """Initialize NotebookLM service.

        Args:
            redis_client: Redis client for caching. If None, caching is disabled.
        """
        self.settings = get_settings()
        self.redis_client = redis_client

    async def query(self, query_text: str) -> NotebookLMResult | None:
        """Query NotebookLM for HS code classification.

        Args:
            query_text: Product description to classify.

        Returns:
            NotebookLMResult with parsed HS code data, or None if service is disabled.

        Raises:
            NotebookLMUnavailableError: If NotebookLM is unavailable.
        """
        if not self.settings.notebooklm_enabled:
            return None

        # Check Redis cache
        cached = await self._get_from_cache(query_text)
        if cached is not None:
            return cached

        # Call NotebookLM SDK (synchronous, wrapped in thread)
        raw_answer = await self._call_sdk(query_text)

        # Parse response
        result = self._parse_response(raw_answer)

        # Cache successful result
        await self._save_to_cache(query_text, result)

        return result

    def _get_client_class(self) -> type:
        """Import and return the NotebookLMClient class.

        Isolated for testability — allows mocking without the SDK installed.
        """
        from notebooklm_tools.core.client import NotebookLMClient

        return NotebookLMClient

    async def _call_sdk(self, query_text: str) -> str:
        """Call NotebookLM SDK via asyncio.to_thread.

        Args:
            query_text: Product description to classify.

        Returns:
            Raw markdown answer from NotebookLM.

        Raises:
            NotebookLMUnavailableError: On any SDK/network failure.
        """
        client_class = self._get_client_class()

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    self._sync_query,
                    client_class,
                    query_text,
                ),
                timeout=self.settings.notebooklm_timeout,
            )
            return result.answer
        except asyncio.TimeoutError:
            raise NotebookLMUnavailableError(reason="timeout")
        except NotebookLMUnavailableError:
            raise
        except Exception as exc:
            reason = self._classify_error(exc)
            raise NotebookLMUnavailableError(reason=reason) from exc

    def _sync_query(self, client_class: type, query_text: str) -> object:
        """Synchronous SDK call to run in a thread.

        Args:
            client_class: NotebookLMClient class.
            query_text: Product description.

        Returns:
            SDK result object with .answer attribute.

        Raises:
            NotebookLMUnavailableError: On HTTP 429, 401, 403 errors.
        """
        try:
            client = client_class()
            return client.query(
                notebook_id=self.settings.notebooklm_notebook_id,
                query_text=query_text,
            )
        except Exception as exc:
            exc_str = str(exc).lower()
            if "429" in exc_str:
                raise NotebookLMUnavailableError(reason="rate_limit") from exc
            if "401" in exc_str or "403" in exc_str:
                raise NotebookLMUnavailableError(reason="auth_error") from exc
            raise

    def _classify_error(self, exc: Exception) -> str:
        """Classify an exception into an error reason.

        Args:
            exc: The exception to classify.

        Returns:
            Error reason string.
        """
        exc_str = str(exc).lower()
        if "429" in exc_str or "rate" in exc_str:
            return "rate_limit"
        if "401" in exc_str or "403" in exc_str or "auth" in exc_str:
            return "auth_error"
        if isinstance(exc, (ConnectionError, OSError)):
            return "service_down"
        return "service_down"

    def _parse_response(self, raw_answer: str) -> NotebookLMResult:
        """Parse NotebookLM response to extract HS code and classification.

        Args:
            raw_answer: Full markdown response from NotebookLM.

        Returns:
            Parsed NotebookLMResult.
        """
        # Extract first HS code match
        hs_match = HS_CODE_PATTERN.search(raw_answer)
        hs_code = hs_match.group(0) if hs_match else None

        # Extract classification reasoning
        classification = self._extract_classification(raw_answer) if hs_code else None

        # Extract practical notes
        practical_notes = self._extract_practical_notes(raw_answer)

        return NotebookLMResult(
            hs_code=hs_code,
            classification=classification,
            practical_notes=practical_notes,
            raw_answer=raw_answer,
        )

    def _extract_classification(self, text: str) -> dict:
        """Extract classification reasoning from response text.

        Args:
            text: NotebookLM response text.

        Returns:
            Dict with reasoning, material, and function fields.
        """
        lines = text.split("\n")
        reasoning_parts: list[str] = []
        material_parts: list[str] = []
        function_parts: list[str] = []

        for line in lines:
            line_lower = line.lower().strip()
            if not line_lower:
                continue
            if any(kw in line_lower for kw in ["material", "chất liệu", "vật liệu"]):
                material_parts.append(line.strip())
            elif any(kw in line_lower for kw in ["function", "chức năng", "công dụng", "use"]):
                function_parts.append(line.strip())
            elif any(
                kw in line_lower
                for kw in ["gri", "classify", "phân loại", "heading", "chapter", "nhóm"]
            ):
                reasoning_parts.append(line.strip())

        return {
            "reasoning": " ".join(reasoning_parts) if reasoning_parts else text[:500],
            "material": " ".join(material_parts) if material_parts else "",
            "function": " ".join(function_parts) if function_parts else "",
        }

    def _extract_practical_notes(self, text: str) -> list[str]:
        """Extract practical notes (bullet points, numbered items) from response.

        Args:
            text: NotebookLM response text.

        Returns:
            List of practical note strings.
        """
        notes: list[str] = []
        for line in text.split("\n"):
            stripped = line.strip()
            # Match bullet points or numbered items about practical guidance
            is_list_item = stripped.startswith(("- ", "* ", "• ")) or re.match(r"^\d+\.", stripped)
            if stripped and is_list_item:
                content = re.sub(r"^[-*•]\s*|\d+\.\s*", "", stripped).strip()
                if content and any(
                    kw in content.lower()
                    for kw in [
                        "fta",
                        "rate",
                        "thuế",
                        "import",
                        "nhập khẩu",
                        "export",
                        "xuất khẩu",
                        "procedure",
                        "thủ tục",
                        "certificate",
                        "c/o",
                        "evfta",
                        "rcep",
                        "cptpp",
                        "duty",
                    ]
                ):
                    notes.append(content)
        return notes

    def _cache_key(self, query_text: str) -> str:
        """Generate Redis cache key for a query.

        Args:
            query_text: The query text.

        Returns:
            Cache key string.
        """
        normalized = query_text.lower().strip()
        query_hash = hashlib.md5(normalized.encode()).hexdigest()
        return f"nlm:{query_hash}"

    async def _get_from_cache(self, query_text: str) -> NotebookLMResult | None:
        """Try to get cached result from Redis.

        Args:
            query_text: The query text.

        Returns:
            Cached NotebookLMResult or None.
        """
        if not self.redis_client:
            return None

        try:
            cached = await self.redis_client.get(self._cache_key(query_text))
            if cached:
                data = json.loads(cached)
                return NotebookLMResult(**data)
        except Exception:
            pass

        return None

    async def _save_to_cache(self, query_text: str, result: NotebookLMResult) -> None:
        """Save result to Redis cache.

        Args:
            query_text: The query text.
            result: The result to cache.
        """
        if not self.redis_client:
            return

        try:
            await self.redis_client.setex(
                self._cache_key(query_text),
                self.settings.notebooklm_cache_ttl,
                json.dumps(asdict(result)),
            )
        except Exception:
            pass
