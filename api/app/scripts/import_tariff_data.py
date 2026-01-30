"""Script to import tariff data from Excel into database."""

import argparse
import asyncio
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.config import get_settings
from app.models.data_version import DataVersion
from app.models.fta_rate import FTARate
from app.models.hs_code import HSCode
from app.services.excel_parser_service import TariffExcelParser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def import_tariff_data(
    excel_file_path: str,
    data_version_name: str,
    dry_run: bool = False
) -> None:
    """Import tariff data from Excel file into database.

    Args:
        excel_file_path: Path to the Excel file
        data_version_name: Name for this data version
        dry_run: If True, parse but don't insert into database
    """
    start_time = time.time()

    # Create database connection
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    logger.info(f"Starting tariff data import from: {excel_file_path}")
    logger.info(f"Data version: {data_version_name}")
    logger.info(f"Dry run mode: {dry_run}")

    try:
        # Parse Excel file
        logger.info("Parsing Excel file...")
        with TariffExcelParser(excel_file_path) as parser:
            hs_code_data_list = parser.parse_all()

        logger.info(f"Parsed {len(hs_code_data_list)} HS codes from Excel")

        if dry_run:
            logger.info("DRY RUN: Would have imported {} HS codes".format(len(hs_code_data_list)))
            # Show sample of parsed data
            if hs_code_data_list:
                sample = hs_code_data_list[0]
                logger.info(f"Sample HS code: {sample}")
            return

        # Import into database
        async with async_session_maker() as session:
            async with session.begin():
                logger.info("Creating data version record...")

                # Create data version
                data_version = DataVersion(
                    name=data_version_name,
                    source_file=Path(excel_file_path).name,
                    is_active=False  # Will be set to True after successful import
                )
                session.add(data_version)
                await session.flush()  # Get the ID

                data_version_id = data_version.id
                logger.info(f"Created data version with ID: {data_version_id}")

                # Batch insert HS codes
                batch_size = 500
                total_imported = 0
                total_fta_rates = 0

                for i in range(0, len(hs_code_data_list), batch_size):
                    batch = hs_code_data_list[i:i + batch_size]

                    # Create HS code objects
                    hs_code_objects = []
                    for hs_data in batch:
                        hs_code = HSCode(
                            code=hs_data.code,
                            description_vn=hs_data.description_vn,
                            description_en=hs_data.description_en,
                            unit=hs_data.unit,
                            duty_rate=float(hs_data.duty_rate),
                            vat_rate=float(hs_data.vat_rate),
                            policy_notes=hs_data.policy_notes,
                            embedding=None,  # Will be populated in Story 1.3
                            data_version_id=data_version_id
                        )
                        hs_code_objects.append(hs_code)

                    # Insert HS codes batch
                    session.add_all(hs_code_objects)
                    await session.flush()  # Get IDs for FTA rates

                    # Create FTA rates for each HS code
                    fta_rate_objects = []
                    for hs_code, hs_data in zip(hs_code_objects, batch):
                        for agreement_code, rate in hs_data.fta_rates.items():
                            fta_rate = FTARate(
                                hs_code_id=hs_code.id,
                                agreement_code=agreement_code,
                                preferential_rate=float(rate),
                                conditions=None  # Can be enhanced later
                            )
                            fta_rate_objects.append(fta_rate)

                    # Insert FTA rates batch
                    if fta_rate_objects:
                        session.add_all(fta_rate_objects)
                        total_fta_rates += len(fta_rate_objects)

                    total_imported += len(hs_code_objects)

                    # Log progress
                    if total_imported % 1000 == 0:
                        logger.info(f"Imported {total_imported}/{len(hs_code_data_list)} HS codes...")

                logger.info(f"Imported {total_imported} HS codes and {total_fta_rates} FTA rates")

                # Mark data version as active
                data_version.is_active = True
                data_version.activated_at = datetime.now(timezone.utc)

                logger.info("Committing transaction...")
                # Commit happens automatically when exiting the context manager

        logger.info("Import completed successfully!")

        # Calculate and log performance metrics
        elapsed_time = time.time() - start_time
        logger.info(f"Total time: {elapsed_time:.2f} seconds")
        logger.info(f"Import rate: {total_imported / elapsed_time:.0f} records/second")

    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        raise
    finally:
        await engine.dispose()


async def verify_import(data_version_name: str) -> None:
    """Verify imported data by querying a sample."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session_maker() as session:
            # Get data version
            result = await session.execute(
                select(DataVersion).where(DataVersion.name == data_version_name)
            )
            data_version = result.scalar_one_or_none()

            if not data_version:
                logger.error(f"Data version '{data_version_name}' not found")
                return

            logger.info(f"Data version: {data_version.name}")
            logger.info(f"  - Source file: {data_version.source_file}")
            logger.info(f"  - Active: {data_version.is_active}")
            logger.info(f"  - Uploaded at: {data_version.uploaded_at}")

            # Count HS codes
            result = await session.execute(
                select(HSCode).where(HSCode.data_version_id == data_version.id)
            )
            hs_codes = result.scalars().all()
            logger.info(f"  - Total HS codes: {len(hs_codes)}")

            # Show sample HS code
            if hs_codes:
                sample = hs_codes[0]
                logger.info(f"\nSample HS code:")
                logger.info(f"  Code: {sample.code}")
                logger.info(f"  Description VN: {sample.description_vn[:50]}...")
                logger.info(f"  Description EN: {sample.description_en[:50]}...")
                logger.info(f"  Duty rate: {sample.duty_rate}%")
                logger.info(f"  VAT rate: {sample.vat_rate}%")

    finally:
        await engine.dispose()


def main() -> None:
    """Main entry point for the import script."""
    parser = argparse.ArgumentParser(description="Import tariff data from Excel")
    parser.add_argument(
        "excel_file",
        help="Path to the Excel file containing tariff data"
    )
    parser.add_argument(
        "--name",
        default="2026 Tariff Schedule",
        help="Name for this data version"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse the file but don't insert into database"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify the import after completion"
    )

    args = parser.parse_args()

    # Run import
    asyncio.run(import_tariff_data(
        excel_file_path=args.excel_file,
        data_version_name=args.name,
        dry_run=args.dry_run
    ))

    # Run verification if requested
    if args.verify and not args.dry_run:
        logger.info("\nVerifying import...")
        asyncio.run(verify_import(args.name))


if __name__ == "__main__":
    main()
