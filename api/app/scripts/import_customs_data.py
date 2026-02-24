"""Script to import customs report data into the knowledge base.

Parses Vietnamese customs import/export report files (XLS/XLSX) and bulk-inserts
verified product-to-HS code mappings into the lookup_records table.

Usage:
    python -m app.scripts.import_customs_data docs/baocaohangchitiet/
    python -m app.scripts.import_customs_data docs/baocaohangchitiet/ --dry-run
    python -m app.scripts.import_customs_data docs/baocaohangchitiet/bchangchitiet-1-dothanh.xls
"""

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.config import get_settings  # noqa: E402
from app.services.customs_import_service import (  # noqa: E402
    CustomsImportService,
    CustomsReportParser,
    ImportResult,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Known company names by file pattern (for traceability notes)
COMPANY_MAP: dict[str, str] = {
    "dothanh": "DKE Vietnam (Do Thanh)",
    "growatt": "Nhom Do Thanh (Growatt)",
    "kde": "Growatt Vietnam (KDE)",
}


def detect_company_name(filename: str) -> str:
    """Detect company name from the filename."""
    lower = filename.lower()
    for key, name in COMPANY_MAP.items():
        if key in lower:
            return name
    return "Unknown"


def print_result(file_name: str, result: ImportResult) -> None:
    """Print a formatted import result summary."""
    logger.info(f"\n{'=' * 60}")
    logger.info(f"File: {file_name}")
    logger.info(f"{'=' * 60}")
    logger.info(f"  Total rows parsed:     {result.total_rows:>8,}")
    logger.info(f"  Records imported:      {result.records_imported:>8,}")
    logger.info(f"  Duplicates skipped:    {result.duplicates_skipped:>8,}")
    logger.info(f"  Unmatched HS codes:    {len(result.unmatched_codes):>8,}")
    logger.info(f"  Errors:                {len(result.errors):>8,}")

    if result.unmatched_codes:
        logger.info("\n  Unmatched HS codes (first 10):")
        for item in result.unmatched_codes[:10]:
            logger.info(
                f"    Row {item['row']}: code={item['code']}, "
                f"product={item['product_name']}"
            )
        if len(result.unmatched_codes) > 10:
            logger.info(
                f"    ... and {len(result.unmatched_codes) - 10} more"
            )


async def import_customs_data(
    path: str,
    dry_run: bool = False,
) -> None:
    """Import customs data from a file or directory.

    Args:
        path: Path to a single file or directory containing XLS/XLSX files.
        dry_run: If True, parse files but don't insert into database.
    """
    start_time = time.time()
    target = Path(path)

    # Collect files to process
    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = sorted(
            list(target.glob("*.xls")) + list(target.glob("*.xlsx"))
        )
        if not files:
            logger.error(f"No .xls or .xlsx files found in {target}")
            return
    else:
        logger.error(f"Path does not exist: {target}")
        return

    logger.info(f"Found {len(files)} file(s) to process")
    logger.info(f"Dry run: {dry_run}")

    # Create database connection
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    grand_total = ImportResult()

    try:
        for file_path in files:
            logger.info(f"\nProcessing: {file_path.name}")
            company_name = detect_company_name(file_path.name)
            logger.info(f"  Company: {company_name}")

            # Parse
            try:
                parser = CustomsReportParser(file_path)
                parsed_rows = parser.parse()
                logger.info(f"  Parsed {len(parsed_rows)} rows")
            except Exception as e:
                logger.error(f"  Parse error: {e}", exc_info=True)
                grand_total.errors.append({
                    "file": file_path.name,
                    "error": str(e),
                    "row": 0,
                })
                continue

            if dry_run:
                result = ImportResult(total_rows=len(parsed_rows))
                print_result(file_path.name, result)
                grand_total.total_rows += result.total_rows
                continue

            # Import
            async with session_factory() as session:
                async with session.begin():
                    service = CustomsImportService(session)
                    result = await service.import_rows(
                        parsed_rows=parsed_rows,
                        source_file=file_path.name,
                        company_name=company_name,
                    )

            print_result(file_path.name, result)

            # Accumulate totals
            grand_total.total_rows += result.total_rows
            grand_total.records_imported += result.records_imported
            grand_total.duplicates_skipped += result.duplicates_skipped
            grand_total.unmatched_codes.extend(result.unmatched_codes)
            grand_total.errors.extend(result.errors)

        # Print grand total
        elapsed = time.time() - start_time
        logger.info(f"\n{'#' * 60}")
        logger.info("GRAND TOTAL")
        logger.info(f"{'#' * 60}")
        logger.info(f"  Files processed:       {len(files):>8,}")
        logger.info(f"  Total rows parsed:     {grand_total.total_rows:>8,}")
        logger.info(f"  Records imported:      {grand_total.records_imported:>8,}")
        logger.info(f"  Duplicates skipped:    {grand_total.duplicates_skipped:>8,}")
        logger.info(f"  Unmatched HS codes:    {len(grand_total.unmatched_codes):>8,}")
        logger.info(f"  Errors:                {len(grand_total.errors):>8,}")
        logger.info(f"  Elapsed time:          {elapsed:>8.2f}s")

        if grand_total.records_imported > 0 and elapsed > 0:
            logger.info(
                f"  Import rate:           "
                f"{grand_total.records_imported / elapsed:>8.0f} rec/s"
            )

    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        raise
    finally:
        await engine.dispose()


def main() -> None:
    """Main entry point for the customs data import script."""
    parser = argparse.ArgumentParser(
        description="Import customs report data into the knowledge base"
    )
    parser.add_argument(
        "path",
        help=(
            "Path to a customs report file (.xls/.xlsx) or a directory "
            "containing such files"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse files but don't insert into database",
    )

    args = parser.parse_args()
    asyncio.run(import_customs_data(path=args.path, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
