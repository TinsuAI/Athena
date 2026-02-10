"""Script to generate embeddings for all HS codes.

This script:
1. Loads all HS codes from the database
2. Generates embeddings for Vietnamese descriptions via OpenRouter API
3. Stores embeddings in the hs_codes.embedding column
4. Creates IVFFlat index for vector similarity search
   (HNSW has a 2000-dim limit; IVFFlat supports larger dimensions like 3072)

Features:
- Batch processing (100 at a time to respect API rate limits)
- Progress logging
- Resumable (skips codes that already have embeddings)
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.redis import redis_pool
from app.models.hs_code import HSCode
from app.models.hs_subheading import HSSubheading
from app.models.hs_heading import HSHeading
from app.services.embedding_service import EmbeddingService

import redis.asyncio as redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Batch size for processing
BATCH_SIZE = 100

# Delay between batches (seconds) to respect rate limits
BATCH_DELAY = 2.0

# Maximum length for policy notes in embedding text
POLICY_NOTES_MAX_LENGTH = 500


def build_embedding_text(hs_code: HSCode) -> str:
    """Build rich embedding text from HS code with chapter, heading, and policy context.

    This provides more context for embeddings than just the description_vn field,
    improving search accuracy by including hierarchical classification information.

    Args:
        hs_code: The HS code object with eager-loaded relationships

    Returns:
        Concatenated text for embedding generation
    """
    parts = []

    # Add chapter context if available
    if hs_code.subheading and hs_code.subheading.heading and hs_code.subheading.heading.chapter:
        chapter = hs_code.subheading.heading.chapter
        parts.append(f"Chương {chapter.chapter_code}: {chapter.name_vn}")

    # Add heading context if available
    if hs_code.subheading and hs_code.subheading.heading:
        heading = hs_code.subheading.heading
        parts.append(f"Nhóm {heading.heading_code}: {heading.name_vn}")

    # Add subheading context if available
    if hs_code.subheading:
        parts.append(f"Phân nhóm {hs_code.subheading.subheading_code}: {hs_code.subheading.name_vn}")

    # Add main descriptions (VN and EN)
    parts.append(hs_code.description_vn)
    if hs_code.description_en:
        parts.append(hs_code.description_en)

    # Add truncated policy notes if available
    if hs_code.policy_notes:
        truncated_notes = hs_code.policy_notes[:POLICY_NOTES_MAX_LENGTH]
        if len(hs_code.policy_notes) > POLICY_NOTES_MAX_LENGTH:
            truncated_notes += "..."
        parts.append(f"Ghi chú: {truncated_notes}")

    return " | ".join(parts)


async def count_hs_codes_without_embeddings(session: AsyncSession) -> int:
    """Count HS codes that don't have embeddings yet."""
    result = await session.execute(
        select(func.count()).select_from(HSCode).where(HSCode.embedding.is_(None))
    )
    return result.scalar() or 0


async def count_total_hs_codes(session: AsyncSession) -> int:
    """Count total HS codes."""
    result = await session.execute(
        select(func.count()).select_from(HSCode)
    )
    return result.scalar() or 0


async def get_hs_codes_without_embeddings(
    session: AsyncSession,
    batch_size: int = BATCH_SIZE,
    force_regenerate: bool = False,
) -> list[HSCode]:
    """Get batch of HS codes that need embeddings.

    Args:
        session: Database session
        batch_size: Number of codes to fetch
        force_regenerate: If True, get all codes regardless of existing embeddings

    Returns:
        List of HS codes with eager-loaded relationships
    """
    query = select(HSCode).options(
        selectinload(HSCode.subheading)
        .selectinload(HSSubheading.heading)
        .selectinload(HSHeading.chapter)
    ).order_by(HSCode.id).limit(batch_size)

    if not force_regenerate:
        query = query.where(HSCode.embedding.is_(None))

    result = await session.execute(query)
    return list(result.scalars().all())


async def update_hs_code_embedding(
    session: AsyncSession,
    hs_code_id: int,
    embedding: list[float],
) -> None:
    """Update embedding for a single HS code."""
    await session.execute(
        update(HSCode)
        .where(HSCode.id == hs_code_id)
        .values(embedding=embedding)
    )


async def create_ivfflat_index(session: AsyncSession) -> None:
    """Create IVFFlat index for vector similarity search.

    Note: pgvector HNSW and IVFFlat indexes have a 2000-dimension limit
    in older versions. For 3072-dimensional embeddings, index creation
    will be skipped if not supported. Vector search will still work
    via sequential scan (acceptable for ~12k rows).
    """
    # Check if any vector index exists on the embedding column
    result = await session.execute(
        text("""
            SELECT i.indexname
            FROM pg_indexes i
            JOIN pg_class c ON c.relname = i.indexname
            JOIN pg_index idx ON idx.indexrelid = c.oid
            JOIN pg_am am ON am.oid = c.relam
            WHERE i.tablename = 'hs_codes'
              AND am.amname IN ('ivfflat', 'hnsw')
              AND EXISTS (
                  SELECT 1 FROM pg_attribute a
                  WHERE a.attrelid = (SELECT oid FROM pg_class WHERE relname = 'hs_codes')
                    AND a.attname = 'embedding'
                    AND a.attnum = ANY(idx.indkey)
              )
        """)
    )
    existing_index = result.scalar()
    if existing_index:
        logger.info(f"Vector index already exists: {existing_index}")
        return

    logger.info("Attempting to create IVFFlat index for embeddings...")
    try:
        # lists = sqrt(rows) is a good starting point; with ~12k rows, lists=100 is reasonable
        await session.execute(
            text("""
                CREATE INDEX idx_hs_codes_embedding_ivfflat
                ON hs_codes
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """)
        )
        await session.commit()
        logger.info("IVFFlat index created successfully")
    except Exception as e:
        if "2000 dimensions" in str(e):
            logger.warning(
                "Could not create vector index: pgvector version does not support "
                "dimensions > 2000. Vector search will use sequential scan instead. "
                "Consider upgrading pgvector to 0.7.0+ for index support."
            )
        else:
            raise


async def generate_embeddings_for_all_hs_codes(force_regenerate: bool = False) -> None:
    """Main function to generate embeddings for all HS codes.

    Args:
        force_regenerate: If True, regenerate embeddings for ALL codes,
            not just those without embeddings.
    """
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create Redis client
    redis_client = redis.Redis(connection_pool=redis_pool)

    # Create embedding service
    embedding_service = EmbeddingService(redis_client=redis_client)

    try:
        async with async_session() as session:
            # Get counts
            total_count = await count_total_hs_codes(session)
            pending_count = await count_hs_codes_without_embeddings(session)
            completed_count = total_count - pending_count

            logger.info(f"Total HS codes: {total_count}")
            logger.info(f"Already processed: {completed_count}")
            logger.info(f"Pending: {pending_count}")

            if force_regenerate:
                logger.info("Force regenerate mode: will regenerate ALL embeddings")
                pending_count = total_count
                completed_count = 0
            elif pending_count == 0:
                logger.info("All HS codes already have embeddings!")
                # Still check/create index
                await create_ivfflat_index(session)
                return

            # Track offset for force-regenerate mode
            offset = 0

            # Process in batches
            batch_num = 0
            processed_in_session = 0

            while True:
                batch_num += 1

                if force_regenerate:
                    # For force-regenerate, get codes by offset
                    result = await session.execute(
                        select(HSCode)
                        .options(
                            selectinload(HSCode.subheading)
                            .selectinload(HSSubheading.heading)
                            .selectinload(HSHeading.chapter)
                        )
                        .order_by(HSCode.id)
                        .offset(offset)
                        .limit(BATCH_SIZE)
                    )
                    hs_codes = list(result.scalars().all())
                    offset += len(hs_codes)
                else:
                    hs_codes = await get_hs_codes_without_embeddings(session, BATCH_SIZE)

                if not hs_codes:
                    break

                logger.info(
                    f"Processing batch {batch_num} ({len(hs_codes)} codes, "
                    f"total processed: {completed_count + processed_in_session}/{total_count})"
                )

                # Prepare texts for batch embedding (with rich context)
                texts = [build_embedding_text(code) for code in hs_codes]

                try:
                    # Generate embeddings in batch
                    embeddings = await embedding_service.generate_batch_embeddings(texts)

                    # Update each HS code with its embedding
                    for hs_code, embedding in zip(hs_codes, embeddings):
                        await update_hs_code_embedding(session, hs_code.id, embedding)

                    await session.commit()
                    processed_in_session += len(hs_codes)

                    logger.info(
                        f"Batch {batch_num} complete. "
                        f"Progress: {completed_count + processed_in_session}/{total_count} "
                        f"({((completed_count + processed_in_session) / total_count * 100):.1f}%)"
                    )

                except Exception as e:
                    logger.error(f"Error processing batch {batch_num}: {e}")
                    await session.rollback()
                    raise

                # Delay between batches to respect rate limits
                if pending_count - processed_in_session > 0:
                    await asyncio.sleep(BATCH_DELAY)

            # Create HNSW index after all embeddings are populated
            await create_ivfflat_index(session)

            # Verify all embeddings are populated
            final_pending = await count_hs_codes_without_embeddings(session)
            if final_pending > 0:
                logger.warning(f"{final_pending} HS codes still missing embeddings!")
            else:
                logger.info("All HS codes now have embeddings!")

            logger.info(
                f"Embedding generation complete. "
                f"Processed {processed_in_session} codes in this session."
            )

    finally:
        await engine.dispose()
        await redis_client.aclose()


async def verify_embeddings() -> dict:
    """Verify embedding population status."""
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            total = await count_total_hs_codes(session)
            without_embeddings = await count_hs_codes_without_embeddings(session)
            with_embeddings = total - without_embeddings

            return {
                "total_hs_codes": total,
                "with_embeddings": with_embeddings,
                "without_embeddings": without_embeddings,
                "completion_percentage": (with_embeddings / total * 100) if total > 0 else 0,
            }
    finally:
        await engine.dispose()


def main():
    """Entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate embeddings for HS codes")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Only verify embedding status, don't generate",
    )
    parser.add_argument(
        "--force-regenerate",
        action="store_true",
        help="Regenerate embeddings for ALL codes (including those with existing embeddings)",
    )
    args = parser.parse_args()

    if args.verify:
        result = asyncio.run(verify_embeddings())
        print(f"\nEmbedding Status:")
        print(f"  Total HS codes: {result['total_hs_codes']}")
        print(f"  With embeddings: {result['with_embeddings']}")
        print(f"  Without embeddings: {result['without_embeddings']}")
        print(f"  Completion: {result['completion_percentage']:.1f}%")
    else:
        asyncio.run(generate_embeddings_for_all_hs_codes(force_regenerate=args.force_regenerate))


if __name__ == "__main__":
    main()
