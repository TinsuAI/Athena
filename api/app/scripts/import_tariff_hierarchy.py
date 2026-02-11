"""Import tariff data with full hierarchy (sections, chapters, headings, subheadings, HS codes)."""

import asyncio
import logging
import sys
import time
from pathlib import Path

from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models.data_version import DataVersion
from app.models.fta_rate import FTARate
from app.models.hs_chapter import HSChapter
from app.models.hs_code import HSCode
from app.models.hs_heading import HSHeading
from app.models.hs_section import HSSection
from app.models.hs_subheading import HSSubheading
from app.models.lookup_record import LookupRecord
from app.services.tariff_hierarchy_parser import TariffHierarchyParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def clear_existing_data(session: AsyncSession) -> None:
    """Clear all existing tariff data."""
    logger.info("Clearing existing data...")

    # Delete in reverse dependency order
    await session.execute(delete(LookupRecord))
    await session.execute(delete(FTARate))
    await session.execute(delete(HSCode))
    await session.execute(delete(HSSubheading))
    await session.execute(delete(HSHeading))
    await session.execute(delete(HSChapter))
    await session.execute(delete(HSSection))
    await session.execute(delete(DataVersion))

    await session.commit()
    logger.info("Existing data cleared")


async def import_tariff_data(
    session: AsyncSession,
    file_path: str,
    version_name: str = "2026 Tariff Schedule"
) -> None:
    """Import tariff data with full hierarchy."""
    start_time = time.time()

    # Create data version
    data_version = DataVersion(
        name=version_name,
        source_file=str(Path(file_path).name),
        is_active=True
    )
    session.add(data_version)
    await session.flush()
    logger.info(f"Created data version: {data_version.name} (id={data_version.id})")

    # Parse the Excel file
    logger.info(f"Parsing Excel file: {file_path}")
    with TariffHierarchyParser(file_path) as parser:
        hierarchy = parser.parse_hierarchy()
        export_fta_rates = parser.parse_export_fta_rates()

    # Import sections
    logger.info("Importing sections...")
    section_id_map: dict[str, int] = {}  # roman -> id
    for section_data in hierarchy.sections:
        section = HSSection(
            section_number=section_data.section_number,
            section_roman=section_data.section_roman,
            name_vn=section_data.name_vn,
            name_en=section_data.name_en,
            notes_vn=section_data.notes_vn,
            notes_en=section_data.notes_en
        )
        session.add(section)
        await session.flush()
        section_id_map[section_data.section_roman] = section.id
    logger.info(f"Imported {len(hierarchy.sections)} sections")

    # Import chapters
    logger.info("Importing chapters...")
    chapter_id_map: dict[str, int] = {}  # chapter_code -> id
    for chapter_data in hierarchy.chapters:
        section_id = section_id_map.get(chapter_data.section_roman)
        if not section_id:
            logger.warning(f"Section {chapter_data.section_roman} not found for chapter {chapter_data.chapter_code}")
            continue

        chapter = HSChapter(
            chapter_code=chapter_data.chapter_code,
            section_id=section_id,
            name_vn=chapter_data.name_vn,
            name_en=chapter_data.name_en,
            notes_vn=chapter_data.notes_vn,
            notes_en=chapter_data.notes_en
        )
        session.add(chapter)
        await session.flush()
        chapter_id_map[chapter_data.chapter_code] = chapter.id
    logger.info(f"Imported {len(chapter_id_map)} chapters")

    # Import headings
    logger.info("Importing headings...")
    heading_id_map: dict[str, int] = {}  # heading_code -> id
    for heading_data in hierarchy.headings:
        chapter_id = chapter_id_map.get(heading_data.chapter_code)
        if not chapter_id:
            logger.warning(f"Chapter {heading_data.chapter_code} not found for heading {heading_data.heading_code}")
            continue

        heading = HSHeading(
            heading_code=heading_data.heading_code,
            chapter_id=chapter_id,
            name_vn=heading_data.name_vn,
            name_en=heading_data.name_en
        )
        session.add(heading)
        await session.flush()
        heading_id_map[heading_data.heading_code] = heading.id
    logger.info(f"Imported {len(heading_id_map)} headings")

    # Import subheadings
    logger.info("Importing subheadings...")
    subheading_id_map: dict[str, int] = {}  # subheading_code -> id
    for subheading_data in hierarchy.subheadings:
        heading_id = heading_id_map.get(subheading_data.heading_code)
        if not heading_id:
            logger.warning(f"Heading {subheading_data.heading_code} not found for subheading {subheading_data.subheading_code}")
            continue

        subheading = HSSubheading(
            subheading_code=subheading_data.subheading_code,
            heading_id=heading_id,
            name_vn=subheading_data.name_vn,
            name_en=subheading_data.name_en,
            indent_level=subheading_data.indent_level
        )
        session.add(subheading)
        await session.flush()
        subheading_id_map[subheading_data.subheading_code] = subheading.id

        if len(subheading_id_map) % 500 == 0:
            logger.info(f"Imported {len(subheading_id_map)} subheadings...")

    logger.info(f"Imported {len(subheading_id_map)} subheadings")

    # Import HS codes
    logger.info("Importing HS codes...")
    hs_codes_imported = 0
    fta_rates_imported = 0
    rcep_yearly_imported = 0
    conditions_populated = 0
    missing_subheadings: set[str] = set()
    hs_code_id_map: dict[str, int] = {}  # code_str -> hs_code.id

    # Counters for new columns
    export_duty_count = 0
    ttdb_count = 0
    bvmt_count = 0
    vat_reduction_count = 0

    for hs_code_data in hierarchy.hs_codes:
        subheading_id = subheading_id_map.get(hs_code_data.subheading_code)
        if not subheading_id:
            missing_subheadings.add(hs_code_data.subheading_code)
            # Still import the HS code without subheading link
            subheading_id = None

        hs_code = HSCode(
            code=hs_code_data.code,
            subheading_id=subheading_id,
            description_vn=hs_code_data.description_vn,
            description_en=hs_code_data.description_en,
            unit=hs_code_data.unit,
            duty_rate=float(hs_code_data.duty_rate),
            vat_rate=float(hs_code_data.vat_rate),
            export_duty_rate=hs_code_data.export_duty_rate,
            special_consumption_tax=hs_code_data.special_consumption_tax,
            environmental_tax=hs_code_data.environmental_tax,
            vat_reduction=hs_code_data.vat_reduction,
            policy_notes=hs_code_data.policy_notes,
            indent_level=hs_code_data.indent_level,
            data_version_id=data_version.id
        )
        session.add(hs_code)
        await session.flush()
        hs_code_id_map[hs_code_data.code] = hs_code.id

        # Track new column population
        if hs_code_data.export_duty_rate:
            export_duty_count += 1
        if hs_code_data.special_consumption_tax:
            ttdb_count += 1
        if hs_code_data.environmental_tax:
            bvmt_count += 1
        if hs_code_data.vat_reduction:
            vat_reduction_count += 1

        # Import FTA rates
        for fta_rate_data in hs_code_data.fta_rates:
            fta_rate = FTARate(
                hs_code_id=hs_code.id,
                agreement_code=fta_rate_data.agreement_code,
                preferential_rate=float(fta_rate_data.preferential_rate),
                conditions=fta_rate_data.conditions,
                rate_year=fta_rate_data.rate_year,
                is_export=fta_rate_data.is_export,
                legal_document=fta_rate_data.legal_document,
                effective_date=fta_rate_data.effective_date,
            )
            session.add(fta_rate)
            fta_rates_imported += 1
            if fta_rate_data.rate_year is not None:
                rcep_yearly_imported += 1
            if fta_rate_data.conditions is not None:
                conditions_populated += 1

        hs_codes_imported += 1
        if hs_codes_imported % 1000 == 0:
            logger.info(f"Imported {hs_codes_imported} HS codes...")
            await session.commit()

    await session.commit()

    # Import export FTA rates (from CPTPP-XK, EV-XK, UKV-XK sheets)
    logger.info("Importing export FTA rates...")
    export_fta_imported = 0
    export_fta_skipped = 0
    for rate_data in export_fta_rates:
        hs_code_str = rate_data.__dict__.get("_hs_code", "")
        hs_code_id = hs_code_id_map.get(hs_code_str)
        if not hs_code_id:
            export_fta_skipped += 1
            continue

        fta_rate = FTARate(
            hs_code_id=hs_code_id,
            agreement_code=rate_data.agreement_code,
            preferential_rate=float(rate_data.preferential_rate),
            is_export=True,
        )
        session.add(fta_rate)
        export_fta_imported += 1

        if export_fta_imported % 500 == 0:
            await session.commit()

    await session.commit()

    if missing_subheadings:
        logger.warning(f"Found {len(missing_subheadings)} HS codes with missing subheadings")
        logger.debug(f"Missing subheadings: {sorted(missing_subheadings)[:20]}...")

    elapsed = time.time() - start_time
    logger.info(f"Import completed successfully!")
    logger.info(f"  - Sections: {len(hierarchy.sections)}")
    logger.info(f"  - Chapters: {len(chapter_id_map)}")
    logger.info(f"  - Headings: {len(heading_id_map)}")
    logger.info(f"  - Subheadings: {len(subheading_id_map)}")
    logger.info(f"  - HS Codes: {hs_codes_imported}")
    logger.info(f"  - FTA Rates (import): {fta_rates_imported}")
    logger.info(f"    - With conditions: {conditions_populated}")
    logger.info(f"    - RCEP yearly: {rcep_yearly_imported}")
    logger.info(f"  - FTA Rates (export): {export_fta_imported} (skipped {export_fta_skipped} unmatched)")
    logger.info(f"  - New columns populated:")
    logger.info(f"    - Export duty rate: {export_duty_count}")
    logger.info(f"    - Special consumption tax (TTDB): {ttdb_count}")
    logger.info(f"    - Environmental tax (BVMT): {bvmt_count}")
    logger.info(f"    - VAT reduction: {vat_reduction_count}")
    logger.info(f"Total time: {elapsed:.2f} seconds")


async def main() -> None:
    """Main entry point."""
    # Default file path
    file_path = "/docs/BIEU-THUE-XNK-2026.xlsx"

    # Check if file exists
    if not Path(file_path).exists():
        logger.error(f"Excel file not found: {file_path}")
        sys.exit(1)

    # Database connection
    database_url = "postgresql+asyncpg://athena:athena@postgres:5432/athena"

    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        await clear_existing_data(session)
        await import_tariff_data(session, file_path)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
