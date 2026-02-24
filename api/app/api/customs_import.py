"""Admin API endpoints for customs report file upload and bulk import."""

import logging
import os
import tempfile
import time
from typing import Any

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.auth import require_admin
from app.repositories.customs_import_repository import CustomsImportRepository
from app.schemas.base import error_response, success_response
from app.schemas.customs_import import (
    CustomsImportPreviewResponse,
    CustomsImportResultResponse,
    ImportBatchResponse,
    KBStatsResponse,
    SampleRow,
)
from app.services.customs_import_service import (
    CustomsImportService,
    CustomsReportParser,
    ParsedRow,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/customs-import",
    tags=["admin", "customs-import"],
)

_ALLOWED_EXTENSIONS = (".xls", ".xlsx")


async def _parse_file(
    file: UploadFile, instance: str
) -> tuple[list[ParsedRow] | None, str | None, dict | None]:
    """Validate, save to temp, and parse an uploaded customs report file.

    Returns:
        (parsed_rows, tmp_path, error_dict) — error_dict is None on success.
        tmp_path is returned so the caller can clean it up in a finally block.
    """
    if not file.filename or not file.filename.lower().endswith(_ALLOWED_EXTENSIONS):
        return None, None, error_response(
            type_uri="https://athena.example/errors/validation",
            title="Invalid File Type",
            status=400,
            detail="Chi chap nhan tep XLS hoac XLSX",
            instance=instance,
        )

    ext = os.path.splitext(file.filename)[1]
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        parser = CustomsReportParser(tmp_path)
        parsed_rows = parser.parse()

        if not parsed_rows:
            return None, tmp_path, error_response(
                type_uri="https://athena.example/errors/validation",
                title="No Data Found",
                status=400,
                detail="Khong tim thay du lieu hop le trong tep. Vui long kiem tra dinh dang tep.",
                instance=instance,
            )

        return parsed_rows, tmp_path, None

    except ValueError as e:
        logger.warning("File parse error: %s", e)
        return None, tmp_path, error_response(
            type_uri="https://athena.example/errors/validation",
            title="Parse Error",
            status=400,
            detail=str(e),
            instance=instance,
        )
    except Exception as e:
        logger.exception("Unexpected error during file parsing: %s", e)
        return None, tmp_path, error_response(
            type_uri="https://athena.example/errors/server-error",
            title="Server Error",
            status=500,
            detail="Loi he thong khi xu ly tep. Vui long thu lai.",
            instance=instance,
        )


@router.post("/upload", response_model=None)
async def upload_customs_report(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Upload a customs report file (XLS/XLSX) and return a preview of the import.

    Parses the file, runs dedup + HS code matching analysis, and returns
    preview data without actually inserting any records. Requires admin role.
    """
    instance = "/api/admin/customs-import/upload"
    parsed_rows, tmp_path, err = await _parse_file(file, instance)
    try:
        if err is not None:
            return err

        service = CustomsImportService(db)
        preview_data = await service.preview_import(parsed_rows)  # type: ignore[arg-type]

        preview = CustomsImportPreviewResponse(
            file_name=file.filename or "",
            total_rows=preview_data["total_rows"],
            sample_rows=[SampleRow(**r) for r in preview_data["sample_rows"]],
            duplicate_count=preview_data["duplicate_count"],
            unmatched_count=preview_data["unmatched_count"],
            ready_to_import_count=preview_data["ready_to_import_count"],
        )

        return success_response(preview.model_dump())

    except Exception as e:
        logger.exception("Unexpected error during file upload: %s", e)
        return error_response(
            type_uri="https://athena.example/errors/server-error",
            title="Server Error",
            status=500,
            detail="Loi he thong khi xu ly tep. Vui long thu lai.",
            instance=instance,
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/execute", response_model=None)
async def execute_customs_import(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Execute customs report import by re-uploading the file.

    Client re-sends the same file for actual import execution. This avoids
    server-side session state (simpler approach per story Dev Notes).
    Requires admin role.
    """
    instance = "/api/admin/customs-import/execute"
    parsed_rows, tmp_path, err = await _parse_file(file, instance)
    try:
        if err is not None:
            return err

        start_time = time.monotonic()

        service = CustomsImportService(db)
        result = await service.import_rows(
            parsed_rows=parsed_rows,  # type: ignore[arg-type]
            source_file=file.filename or "unknown",
            company_name=current_user.get("email", "admin_upload"),
            imported_by_user_id=current_user.get("id"),
        )

        elapsed = time.monotonic() - start_time

        response = CustomsImportResultResponse(
            file_name=file.filename or "",
            total_rows=result.total_rows,
            records_imported=result.records_imported,
            duplicates_skipped=result.duplicates_skipped,
            unmatched_codes=result.unmatched_codes,
            errors=result.errors,
            elapsed_seconds=round(elapsed, 2),
            batch_id=result.batch_id,
        )

        return success_response(response.model_dump())

    except Exception as e:
        logger.exception("Unexpected error during import execution: %s", e)
        await db.rollback()
        return error_response(
            type_uri="https://athena.example/errors/server-error",
            title="Server Error",
            status=500,
            detail="Loi he thong khi nhap du lieu. Vui long thu lai.",
            instance=instance,
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/history", response_model=None)
async def get_import_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Get paginated history of customs data imports.

    Returns list of import batches with user email, ordered by most recent first.
    Requires admin role.
    """
    try:
        repo = CustomsImportRepository(db)
        items, total = await repo.get_import_history(limit=limit, offset=offset)

        return success_response({
            "items": [ImportBatchResponse(**item).model_dump() for item in items],
            "total": total,
        })
    except Exception as e:
        logger.exception("Error fetching import history: %s", e)
        return error_response(
            type_uri="https://athena.example/errors/server-error",
            title="Server Error",
            status=500,
            detail="Loi he thong khi tai lich su nhap du lieu.",
            instance="/api/admin/customs-import/history",
        )


@router.get("/stats", response_model=None)
async def get_kb_stats(
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Get knowledge base quality statistics.

    Returns total verified records, breakdown by search method,
    top chapters by coverage, and recent imports. Requires admin role.
    """
    try:
        repo = CustomsImportRepository(db)
        stats = await repo.get_kb_stats()
        recent_imports = await repo.get_recent_imports(limit=5)

        response = KBStatsResponse(
            total_verified=stats["total_verified"],
            breakdown_by_method=stats["breakdown_by_method"],
            top_chapters=stats["top_chapters"],
            recent_imports=[ImportBatchResponse(**item) for item in recent_imports],
        )

        return success_response(response.model_dump())
    except Exception as e:
        logger.exception("Error fetching KB stats: %s", e)
        return error_response(
            type_uri="https://athena.example/errors/server-error",
            title="Server Error",
            status=500,
            detail="Loi he thong khi tai thong ke co so kien thuc.",
            instance="/api/admin/customs-import/stats",
        )
