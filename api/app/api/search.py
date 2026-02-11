"""Search API endpoint for hybrid HS code search."""

import logging
import time
from typing import Any

import redis.asyncio as redis
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.redis import get_redis
from app.schemas.base import ApiResponse, error_response, success_response
from app.schemas.search import (
    ClassificationSchema,
    ProcessLogEntry,
    SearchRequest,
    SearchResponseData,
)
from app.core.config import get_settings
from app.models.hs_code import HSCode
from app.models.hs_heading import HSHeading
from app.models.hs_subheading import HSSubheading
from app.models.lookup_record import LookupRecord
from app.repositories.lookup_record_repository import (
    LookupRecordRepository,
    compute_query_hash,
)
from app.services.classification_analyzer import ClassificationAnalyzer
from app.services.llm_reasoning_service import LLMReasoningService
from app.services.query_enhancement_service import QueryEnhancementService
from app.services.reranking_service import RerankingService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.search_cache import CachedSearchResult, SearchCacheService
from app.services.search_service import SearchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["search"])


def _format_hs_code(code: str) -> str:
    """Format HS code with dots (e.g., 74182000 -> 7418.20.00)."""
    if len(code) == 8:
        return f"{code[:4]}.{code[4:6]}.{code[6:]}"
    return code


def _format_rate(rate: float) -> str:
    """Format rate as percentage string."""
    if rate == int(rate):
        return f"{int(rate)}%"
    return f"{rate}%"


def _detect_query_language(query: str) -> str | None:
    """Detect query language based on character ranges (best-effort heuristic).

    Returns: 'vi', 'en', 'zh', or None if uncertain
    """
    if not query:
        return None

    # Count character types
    vietnamese_chars = sum(1 for c in query if c in 'àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ')
    chinese_chars = sum(1 for c in query if '\u4e00' <= c <= '\u9fff')
    latin_chars = sum(1 for c in query if c.isalpha() and ord(c) < 128)

    # Simple heuristic: majority character type
    if vietnamese_chars > 0:
        return 'vi'
    elif chinese_chars > 0:
        return 'zh'
    elif latin_chars > 0:
        return 'en'

    return None


async def _record_lookup(
    db: AsyncSession,
    query: str,
    matched_hs_code_id: int | None,
    confidence_score: float | None,
    search_method: str,
    classification_data: dict | None = None,
    practical_notes: list[str] | None = None,
    process_logs: list[dict] | None = None,
) -> int | None:
    """Record a search lookup for the knowledge base (best-effort, failures logged).

    Returns:
        The lookup record ID, or None if recording failed.
    """
    try:
        repo = LookupRecordRepository(session=db)
        query_hash = compute_query_hash(query)

        # Dedup: check if same query hash exists within 24h
        existing = await repo.find_by_query_hash(query_hash)
        if existing:
            # Update JSONB fields with fresh data
            existing.classification_data = classification_data
            existing.practical_notes = practical_notes
            existing.process_logs = process_logs
            await repo.update(existing)
            return existing.id

        # Detect query language
        query_language = _detect_query_language(query)

        record = LookupRecord(
            query_text=query,
            query_hash=query_hash,
            query_language=query_language,
            matched_hs_code_id=matched_hs_code_id,
            is_verified=False,
            confidence_score=confidence_score,
            search_method=search_method,
            classification_data=classification_data,
            practical_notes=practical_notes,
            process_logs=process_logs,
        )
        created = await repo.create(record)
        return created.id
    except Exception as e:
        logger.warning(
            "Failed to record lookup",
            extra={
                "query_preview": query[:50],
                "matched_hs_code_id": matched_hs_code_id,
                "error": str(e),
            },
            exc_info=True,
        )
        return None


@router.post(
    "/search",
    response_model=ApiResponse[SearchResponseData],
    summary="Search for HS codes",
    description="""
    Search for HS codes using product descriptions or exact codes.

    **Features:**
    - Supports Vietnamese, English, and Chinese (best effort) product descriptions
    - Hybrid search: vector similarity + fuzzy text + exact match
    - Returns classification analysis with material and function reasoning
    - Includes practical import notes and FTA optimization hints

    **Examples:**
    - Vietnamese: "Thanh treo khăn MITO, mã A2018ANE, bằng đồng mạ chrome"
    - English: "copper bathroom towel rack, chrome plated"
    - HS Code: "7418.20.00" or "74182000"
    """,
)
async def search_hs_codes(
    request: Request,
    body: SearchRequest,
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),  # type: ignore[type-arg]
) -> dict[str, Any]:
    """Search for HS codes with classification analysis.

    Args:
        request: FastAPI request (for logging)
        body: Search request with query
        db: Database session
        redis_client: Redis client for caching

    Returns:
        Best matching HS code with classification analysis
    """
    settings = get_settings()
    start_time = time.time()
    process_logs: list[ProcessLogEntry] = []

    def add_log(step: str, status: str, message: str, duration_ms: int | None = None, details: dict | None = None):
        process_logs.append(ProcessLogEntry(
            step=step,
            status=status,
            message=message,
            duration_ms=duration_ms,
            details=details,
        ))

    # Log search request (anonymized - NFR-M3)
    logger.info(
        "Search request",
        extra={
            "query_length": len(body.query),
            "limit": body.limit,
            "client_ip": request.client.host if request.client else "unknown",
        }
    )

    add_log("init", "started", f"Search initiated for query: {body.query[:100]}{'...' if len(body.query) > 100 else ''}")

    try:
        # Create services
        search_service = SearchService(session=db, redis_client=redis_client)
        cache_service = SearchCacheService(redis_client=redis_client)

        # Create LLM reasoning service if API key is available
        llm_service = None
        model_name = body.model or settings.llm_reasoning_model
        if settings.openrouter_api_key:
            llm_service = LLMReasoningService(
                redis_client=redis_client,
                model=body.model,
            )
            add_log("init", "completed", f"LLM service initialized with model: {model_name}")
        else:
            add_log("init", "skipped", "No OPENROUTER_API_KEY, LLM services disabled")

        analyzer = ClassificationAnalyzer(llm_service=llm_service)

        # Create enhancement and reranking services if enabled
        enhancement_service = None
        reranking_service = None
        if settings.openrouter_api_key:
            if settings.enable_query_enhancement:
                enhancement_service = QueryEnhancementService(
                    redis_client=redis_client,
                    model=body.model,
                )
                add_log("init", "completed", "Query enhancement service enabled")
            else:
                add_log("init", "skipped", "Query enhancement disabled in config")
            if settings.enable_reranking:
                reranking_service = RerankingService(
                    redis_client=redis_client,
                    model=body.model,
                )
                add_log("init", "completed", f"Reranking service enabled (candidates: {settings.reranking_candidates})")
            else:
                add_log("init", "skipped", "Reranking disabled in config")

        # --- Knowledge Base Lookup (NEW - primary search) ---
        try:
            kb_service = KnowledgeBaseService(session=db)

            kb_exact_start = time.time()
            add_log("kb_exact_lookup", "started", "Checking knowledge base for exact match...")
            kb_result = await kb_service.lookup(body.query)
            kb_duration = int((time.time() - kb_exact_start) * 1000)

            if kb_result:
                match_label = f"KB {kb_result.match_type} match"
                add_log(
                    f"kb_{kb_result.match_type}_lookup",
                    "completed",
                    f"{match_label} found (confidence: {kb_result.confidence}, similarity: {kb_result.similarity_score:.2f})",
                    duration_ms=kb_duration,
                    details={"match_type": kb_result.match_type, "confidence": kb_result.confidence, "similarity": kb_result.similarity_score},
                )

                # Load full HS code object for classification
                hs_result = await db.execute(
                    select(HSCode)
                    .where(HSCode.id == kb_result.hs_code_id)
                    .options(
                        selectinload(HSCode.fta_rates),
                        selectinload(HSCode.subheading).selectinload(HSSubheading.heading).selectinload(HSHeading.chapter),
                    )
                )
                hs_code_obj = hs_result.scalar_one_or_none()

                if hs_code_obj:
                    # Generate classification analysis (same as existing flow)
                    classify_start = time.time()
                    add_log("classification", "started", f"Generating classification reasoning with LLM (model: {model_name})...")
                    analysis = await analyzer.analyze_async(body.query, hs_code_obj)
                    classify_duration = int((time.time() - classify_start) * 1000)
                    add_log("classification", "completed", f"Classification reasoning generated (model: {model_name})",
                            duration_ms=classify_duration,
                            details={"model": model_name, "material": analysis.material, "function": analysis.function})

                    total_duration = int((time.time() - start_time) * 1000)
                    add_log("complete", "completed", f"Search completed (from KB {kb_result.match_type}): {_format_hs_code(hs_code_obj.code)}",
                            duration_ms=total_duration)

                    verified_at_str = kb_result.verified_at.isoformat() if kb_result.verified_at else None
                    verified_by_str = str(kb_result.verified_by_user_id) if kb_result.verified_by_user_id else None

                    response_data = SearchResponseData(
                        hs_code=_format_hs_code(hs_code_obj.code),
                        description=hs_code_obj.description_vn,
                        duty_rate=_format_rate(float(hs_code_obj.duty_rate)),
                        vat_rate=_format_rate(float(hs_code_obj.vat_rate)),
                        classification=ClassificationSchema(
                            material=analysis.material,
                            function=analysis.function,
                        ),
                        practical_notes=analysis.practical_notes,
                        confidence=kb_result.confidence,
                        process_logs=process_logs,
                        source="knowledge_base",
                        is_verified=True,
                        verified_by=verified_by_str,
                        verified_at=verified_at_str,
                    )

                    logger.info(
                        "Search completed from knowledge base",
                        extra={"duration_ms": total_duration, "match_type": kb_result.match_type}
                    )

                    # Record lookup with search_method="knowledge_base"
                    lookup_id = await _record_lookup(
                        db=db,
                        query=body.query,
                        matched_hs_code_id=hs_code_obj.id,
                        confidence_score=kb_result.confidence,
                        search_method="knowledge_base",
                        classification_data={"material": analysis.material, "function": analysis.function},
                        practical_notes=analysis.practical_notes,
                        process_logs=[log.model_dump() for log in process_logs],
                    )
                    response_data.lookup_id = lookup_id

                    return success_response(response_data.model_dump())
                else:
                    add_log("kb_exact_lookup", "failed", f"KB matched record but HS code id={kb_result.hs_code_id} not found in hs_codes table",
                            duration_ms=kb_duration)
            else:
                add_log("kb_exact_lookup", "completed", "No KB match found, falling back to AI search", duration_ms=kb_duration)
        except Exception as e:
            kb_duration = int((time.time() - kb_exact_start) * 1000) if 'kb_exact_start' in locals() else 0
            add_log("kb_exact_lookup", "failed", f"KB lookup failed: {str(e)}, falling back to AI search", duration_ms=kb_duration)
            logger.warning("KB lookup failed, continuing with AI search", extra={"error": str(e)}, exc_info=True)

        # --- AI Fallback: Existing search flow ---
        # Check cache first
        cache_start = time.time()
        add_log("cache", "started", "Checking search cache...")
        cached_results = await cache_service.get(body.query)
        cache_duration = int((time.time() - cache_start) * 1000)

        if cached_results:
            logger.info("Cache hit for search query")
            # Show all cached candidates
            cached_candidates = [
                {"hs_code": _format_hs_code(r.hs_code), "description": r.description_vn[:80], "confidence": r.confidence}
                for r in cached_results
            ]
            add_log("cache", "completed", f"Cache HIT - found {len(cached_results)} cached results",
                    duration_ms=cache_duration,
                    details={"cached_candidates": cached_candidates})

            # Skip enhancement and reranking for cached results
            add_log("enhancement", "skipped", "Using cached results, enhancement not needed")
            add_log("search", "skipped", "Using cached results")
            add_log("reranking", "skipped", "Using cached results, reranking not needed")

            # Convert cached result to response (use first result)
            if cached_results:
                best_cached = cached_results[0]
                add_log("result", "completed", f"Best cached result: {_format_hs_code(best_cached.hs_code)}",
                        details={"hs_code": _format_hs_code(best_cached.hs_code),
                                 "description": best_cached.description_vn,
                                 "confidence": best_cached.confidence})

                # We still need to generate classification analysis from query
                # Load HS code to get full object for analysis
                result = await db.execute(
                    select(HSCode)
                    .where(HSCode.code == best_cached.hs_code.replace(".", ""))
                    .options(
                        selectinload(HSCode.fta_rates),
                        selectinload(HSCode.subheading).selectinload(HSSubheading.heading).selectinload(HSHeading.chapter),
                    )
                )
                hs_code_obj = result.scalar_one_or_none()

                if hs_code_obj:
                    # Generate classification analysis
                    classify_start = time.time()
                    add_log("classification", "started", f"Generating classification reasoning with LLM (model: {model_name})...")
                    analysis = await analyzer.analyze_async(body.query, hs_code_obj)
                    classify_duration = int((time.time() - classify_start) * 1000)
                    add_log("classification", "completed", f"Classification reasoning generated (model: {model_name})",
                            duration_ms=classify_duration,
                            details={"model": model_name, "material": analysis.material, "function": analysis.function})

                    duration = time.time() - start_time
                    add_log("complete", "completed", f"Search completed (from cache): {_format_hs_code(best_cached.hs_code)}",
                            duration_ms=int(duration * 1000))

                    response_data = SearchResponseData(
                        hs_code=_format_hs_code(best_cached.hs_code),
                        description=best_cached.description_vn,
                        duty_rate=_format_rate(best_cached.duty_rate),
                        vat_rate=_format_rate(best_cached.vat_rate),
                        classification=ClassificationSchema(
                            material=analysis.material,
                            function=analysis.function,
                        ),
                        practical_notes=analysis.practical_notes,
                        confidence=best_cached.confidence,
                        process_logs=process_logs,
                        source="ai_suggestion",
                        is_verified=False,
                    )

                    logger.info(
                        "Search completed from cache",
                        extra={"duration_ms": int(duration * 1000)}
                    )

                    # Record lookup for knowledge base
                    lookup_id = await _record_lookup(
                        db=db,
                        query=body.query,
                        matched_hs_code_id=hs_code_obj.id,
                        confidence_score=best_cached.confidence,
                        search_method="exact" if best_cached.is_exact_match else "vector",
                        classification_data={"material": analysis.material, "function": analysis.function},
                        practical_notes=analysis.practical_notes,
                        process_logs=[log.model_dump() for log in process_logs],
                    )
                    response_data.lookup_id = lookup_id

                    return success_response(response_data.model_dump())
        else:
            add_log("cache", "completed", "Cache MISS - will perform full search", duration_ms=cache_duration)

        # Enhance query if service is available
        search_query = body.query
        enhanced_details = None
        if enhancement_service:
            enhance_start = time.time()
            add_log("enhancement", "started", f"Enhancing query with LLM (model: {model_name})...")
            try:
                enhanced = await enhancement_service.enhance_query(body.query)
                # Use enhanced query for better embedding matches
                search_query = enhanced.enhanced_query
                enhance_duration = int((time.time() - enhance_start) * 1000)
                enhanced_details = {
                    "model": model_name,
                    "original_query": body.query,
                    "enhanced_query": enhanced.enhanced_query,
                    "material_keywords": enhanced.material_keywords,
                    "function_keywords": enhanced.function_keywords,
                    "category": enhanced.category,
                    "likely_chapters": enhanced.likely_chapters,
                }
                add_log("enhancement", "completed", f"Query enhanced successfully (model: {model_name})", duration_ms=enhance_duration, details=enhanced_details)
            except Exception as e:
                enhance_duration = int((time.time() - enhance_start) * 1000)
                add_log("enhancement", "failed", f"Enhancement failed: {str(e)}", duration_ms=enhance_duration)
                logger.warning(f"Query enhancement failed, using original: {e}")
        else:
            add_log("enhancement", "skipped", "Enhancement service not available")

        # Determine search limit - get more candidates if reranking is enabled
        search_limit = settings.reranking_candidates if reranking_service else body.limit

        # Perform search
        search_start = time.time()
        add_log("search", "started", f"Searching with query (limit={search_limit})...")
        results = await search_service.search(
            query=search_query,
            limit=search_limit,
        )
        search_duration = int((time.time() - search_start) * 1000)

        # Log search duration
        duration = time.time() - start_time
        logger.info(
            "Search completed",
            extra={
                "duration_ms": int(duration * 1000),
                "results_count": len(results),
            }
        )

        # Handle no results
        if not results:
            add_log("search", "completed", "No results found", duration_ms=search_duration)
            add_log("complete", "failed", "Search completed with no results")

            # Record lookup even for no-results (valuable for KB)
            # No lookup_id returned in error responses
            await _record_lookup(
                db=db,
                query=body.query,
                matched_hs_code_id=None,
                confidence_score=None,
                search_method="vector",
                classification_data=None,
                practical_notes=None,
                process_logs=[log.model_dump() for log in process_logs],
            )

            return error_response(
                type_uri="https://athena.example/errors/no-results",
                title="No Results",
                status=status.HTTP_404_NOT_FOUND,
                detail="No matching HS code found. Try using more specific product details (material, function, industry)",
                instance="/api/search",
            )

        # Log search results
        search_candidates = [
            {"hs_code": _format_hs_code(r.hs_code), "description": r.description_vn[:80], "confidence": r.confidence}
            for r in results[:10]  # Top 10 for logging
        ]
        add_log("search", "completed", f"Found {len(results)} candidates", duration_ms=search_duration, details={"candidates": search_candidates})

        # Rerank results if service is available
        best_result = results[0]
        original_best = _format_hs_code(results[0].hs_code)
        if reranking_service and len(results) > 1:
            rerank_start = time.time()
            add_log("reranking", "started", f"Reranking {len(results)} candidates with LLM (model: {model_name})...")
            try:
                # Prepare candidates for reranking
                candidates = []
                for r in results:
                    hs_code_obj = r.hs_code_full
                    candidate = {
                        "hs_code": r.hs_code,
                        "description_vn": r.description_vn,
                    }
                    # Add chapter/heading info if available
                    if hs_code_obj and hs_code_obj.subheading:
                        heading = hs_code_obj.subheading.heading
                        if heading:
                            candidate["heading_info"] = f"{heading.heading_code}: {heading.name_vn}"
                            if heading.chapter:
                                candidate["chapter_info"] = f"{heading.chapter.chapter_code}: {heading.chapter.name_vn}"
                    candidates.append(candidate)

                # Use original query for reranking (not enhanced)
                rerank_result = await reranking_service.rerank(body.query, candidates)
                rerank_duration = int((time.time() - rerank_start) * 1000)

                if rerank_result:
                    reranked_best = _format_hs_code(rerank_result.best_code)
                    changed = rerank_result.best_code != results[0].hs_code
                    # Find the reranked best result
                    for r in results:
                        if r.hs_code == rerank_result.best_code:
                            best_result = r
                            break
                    add_log("reranking", "completed",
                        f"Reranked: {reranked_best} {'(CHANGED from ' + original_best + ')' if changed else '(unchanged)'} (model: {model_name})",
                        duration_ms=rerank_duration,
                        details={
                            "model": model_name,
                            "original_best": original_best,
                            "reranked_best": reranked_best,
                            "changed": changed,
                            "reasoning": rerank_result.reasoning,
                        }
                    )
                else:
                    add_log("reranking", "failed", f"Reranking returned no result (model: {model_name}), using original order", duration_ms=rerank_duration)
            except Exception as e:
                rerank_duration = int((time.time() - rerank_start) * 1000)
                add_log("reranking", "failed", f"Reranking failed: {str(e)}", duration_ms=rerank_duration)
                logger.warning(f"Reranking failed, using original order: {e}")
        else:
            if not reranking_service:
                add_log("reranking", "skipped", "Reranking service not available")
            else:
                add_log("reranking", "skipped", "Only 1 result, skipping reranking")

        # Cache the results for future queries
        cached_items = [
            CachedSearchResult(
                hs_code=r.hs_code,
                description_vn=r.description_vn,
                description_en=r.description_en,
                duty_rate=r.duty_rate,
                vat_rate=r.vat_rate,
                unit=r.unit,
                confidence=r.confidence,
                is_exact_match=r.is_exact_match,
            )
            for r in results
        ]
        await cache_service.set(body.query, cached_items)

        # Get full HS code object for classification analysis
        hs_code_obj = best_result.hs_code_full

        # Add result selection log
        add_log("result", "completed", f"Selected best result: {_format_hs_code(best_result.hs_code)}",
                details={"hs_code": _format_hs_code(best_result.hs_code),
                         "description": best_result.description_vn,
                         "confidence": best_result.confidence})

        # Generate classification analysis
        classify_start = time.time()
        add_log("classification", "started", f"Generating classification reasoning with LLM (model: {model_name})...")
        analysis = await analyzer.analyze_async(body.query, hs_code_obj)
        classify_duration = int((time.time() - classify_start) * 1000)
        add_log("classification", "completed", f"Classification reasoning generated (model: {model_name})",
                duration_ms=classify_duration,
                details={"model": model_name, "material": analysis.material, "function": analysis.function})

        # Final completion log
        total_duration = int((time.time() - start_time) * 1000)
        add_log("complete", "completed", f"Search completed: {_format_hs_code(best_result.hs_code)}",
                duration_ms=total_duration,
                details={"total_steps": len(process_logs) + 1,
                         "final_hs_code": _format_hs_code(best_result.hs_code),
                         "confidence": best_result.confidence})

        # Build response
        response_data = SearchResponseData(
            hs_code=_format_hs_code(best_result.hs_code),
            description=best_result.description_vn,
            duty_rate=_format_rate(best_result.duty_rate),
            vat_rate=_format_rate(best_result.vat_rate),
            classification=ClassificationSchema(
                material=analysis.material,
                function=analysis.function,
            ),
            practical_notes=analysis.practical_notes,
            confidence=best_result.confidence,
            process_logs=process_logs,
            source="ai_suggestion",
            is_verified=False,
        )

        # Record lookup for knowledge base
        hs_code_id = None
        if best_result.hs_code_full and hasattr(best_result.hs_code_full, "id"):
            hs_code_id = best_result.hs_code_full.id
        lookup_id = await _record_lookup(
            db=db,
            query=body.query,
            matched_hs_code_id=hs_code_id,
            confidence_score=best_result.confidence,
            search_method="exact" if best_result.is_exact_match else "vector",
            classification_data={"material": analysis.material, "function": analysis.function},
            practical_notes=analysis.practical_notes,
            process_logs=[log.model_dump() for log in process_logs],
        )
        response_data.lookup_id = lookup_id

        return success_response(response_data.model_dump())

    except ValueError as e:
        # Invalid input (empty query, etc.)
        return error_response(
            type_uri="https://athena.example/errors/invalid-input",
            title="Invalid Input",
            status=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
            instance="/api/search",
        )

    except Exception as e:
        logger.exception("Search error")
        return error_response(
            type_uri="https://athena.example/errors/internal-error",
            title="Internal Error",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your search",
            instance="/api/search",
        )