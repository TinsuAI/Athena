"""Script to generate embeddings for all HS codes.

This script:
1. Loads all HS codes from the database
2. Generates embeddings for Vietnamese descriptions via OpenRouter API
3. Stores embeddings in the hs_codes.embedding column
4. Creates HNSW index for vector similarity search

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

from app.core.config import get_settings
from app.core.redis import redis_pool
from app.models.hs_code import HSCode
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
) -> list[HSCode]:
    """Get batch of HS codes that don't have embeddings yet."""
    result = await session.execute(
        select(HSCode)
        .where(HSCode.embedding.is_(None))
        .order_by(HSCode.id)
        .limit(batch_size)
    )
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


async def create_hnsw_index(session: AsyncSession) -> None:
    """Create HNSW index for vector similarity search.

    Only creates if index doesn't already exist.
    """
    # Check if any HNSW index exists on the embedding column
    result = await session.execute(
        text("""
            SELECT i.indexname
            FROM pg_indexes i
            JOIN pg_class c ON c.relname = i.indexname
            JOIN pg_index idx ON idx.indexrelid = c.oid
            JOIN pg_am am ON am.oid = c.relam
            WHERE i.tablename = 'hs_codes'
              AND am.amname = 'hnsw'
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
        logger.info(f"HNSW index already exists: {existing_index}")
        return

    logger.info("Creating HNSW index for embeddings...")
    await session.execute(
        text("""
            CREATE INDEX hs_codes_embedding_hnsw_idx
            ON hs_codes
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
        """)
    )
    await session.commit()
    logger.info("HNSW index created successfully")


async def generate_embeddings_for_all_hs_codes() -> None:
    """Main function to generate embeddings for all HS codes."""
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

            if pending_count == 0:
                logger.info("All HS codes already have embeddings!")
                # Still check/create index
                await create_hnsw_index(session)
                return

            # Process in batches
            batch_num = 0
            processed_in_session = 0

            while True:
                batch_num += 1
                hs_codes = await get_hs_codes_without_embeddings(session, BATCH_SIZE)

                if not hs_codes:
                    break

                logger.info(
                    f"Processing batch {batch_num} ({len(hs_codes)} codes, "
                    f"total processed: {completed_count + processed_in_session}/{total_count})"
                )

                # Prepare texts for batch embedding
                texts = [code.description_vn for code in hs_codes]

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
            await create_hnsw_index(session)

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
    args = parser.parse_args()

    if args.verify:
        result = asyncio.run(verify_embeddings())
        print(f"\nEmbedding Status:")
        print(f"  Total HS codes: {result['total_hs_codes']}")
        print(f"  With embeddings: {result['with_embeddings']}")
        print(f"  Without embeddings: {result['without_embeddings']}")
        print(f"  Completion: {result['completion_percentage']:.1f}%")
    else:
        asyncio.run(generate_embeddings_for_all_hs_codes())


if __name__ == "__main__":
    main()
