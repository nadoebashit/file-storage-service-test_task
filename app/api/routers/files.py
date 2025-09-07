import mimetypes
from uuid import uuid4
from typing import Optional

from fastapi import APIRouter, Depends, File as FileUpload, Form, HTTPException, UploadFile, Query, status
from fastapi_pagination import Page, add_pagination, paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select, update, delete

from app.core.deps import get_current_user, get_db
from app.db.models.user import User
from app.db.models.file import File
from app.db.models.enums import FileStatus, UserRole, Visibility
from app.schemas.file import FileOut, UploadResponse, VisibilityIn
from app.services.storage_s3 import S3Client
from app.tasks.metadata import extract_metadata_task
from app.utils.validators import ensure_upload_allowed
from app.utils.magic import sniff_mime, ensure_mime_matches_ext
from fastapi.responses import RedirectResponse

router = APIRouter()


content = await file.read()
size = len(content)
mime = file.content_type or (mimetypes.guess_type(filename)[0] or "application/octet-stream")

# Проверка фактического MIME по сигнатуре
detected = sniff_mime(content)
if not ensure_mime_matches_ext(ext, detected):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"File content type mismatch: .{ext} vs {detected}",
    )

def _visibility_filter(user: User):
    if user.role in (UserRole.ADMIN, UserRole.MANAGER):
        return True
    return or_(
        File.owner_id == user.id,
        File.visibility == Visibility.PUBLIC,
        and_(File.visibility == Visibility.DEPARTMENT, File.department_id == user.department_id),
    )


def _ensure_read_access(user: User, rec: File):
    if user.role in (UserRole.ADMIN, UserRole.MANAGER):
        return
    allowed = (
        rec.owner_id == user.id
        or rec.visibility == Visibility.PUBLIC
        or (rec.visibility == Visibility.DEPARTMENT and rec.department_id == user.department_id)
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="Forbidden")


def _ensure_delete_access(user: User, rec: File):
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.MANAGER:
        if rec.department_id != user.department_id:
            raise HTTPException(status_code=403, detail="Managers can delete only own department files")
        return
    # USER
    if rec.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Users can delete only own files")


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    visibility: VisibilityIn = Form(...),
    file: UploadFile = FileUpload(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filename = file.filename or "upload.bin"
    ext = (filename.split(".")[-1]).lower() if "." in filename else ""
    content = await file.read()
    size = len(content)
    mime = file.content_type or (mimetypes.guess_type(filename)[0] or "application/octet-stream")

    final_visibility = ensure_upload_allowed(current_user.role.value, ext, size, visibility.value)

    s3_key = f"{current_user.department_id}/{current_user.id}/{uuid4()}.{ext}"
    s3 = S3Client()
    from io import BytesIO

    s3.upload_fileobj(s3_key, BytesIO(content))

    rec = File(
        owner_id=current_user.id,
        department_id=current_user.department_id,
        filename_original=filename,
        s3_key=s3_key,
        mime_type=mime,
        ext=ext,
        size_bytes=size,
        visibility=Visibility(final_visibility),
        status=FileStatus.PENDING,
        metadata={},
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)

    # Celery task
    extract_metadata_task.delay(rec.id)

    return UploadResponse(
        file=FileOut(
            id=rec.id,
            filename_original=rec.filename_original,
            visibility=rec.visibility.value,
            status=rec.status.value,
            size_bytes=rec.size_bytes,
            mime_type=rec.mime_type,
            ext=rec.ext,
            download_count=rec.download_count,
            metadata=rec.metadata,
        )
    )


@router.get("/{file_id}", response_model=FileOut)
async def get_file_info(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rec = await db.scalar(select(File).where(File.id == file_id))
    if not rec:
        raise HTTPException(status_code=404, detail="File not found")
    _ensure_read_access(current_user, rec)
    return FileOut(
        id=rec.id,
        filename_original=rec.filename_original,
        visibility=rec.visibility.value,
        status=rec.status.value,
        size_bytes=rec.size_bytes,
        mime_type=rec.mime_type,
        ext=rec.ext,
        download_count=rec.download_count,
        metadata=rec.metadata,
    )


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rec = await db.scalar(select(File).where(File.id == file_id))
    if not rec:
        raise HTTPException(status_code=404, detail="File not found")
    _ensure_read_access(current_user, rec)

    await db.execute(update(File).where(File.id == file_id).values(download_count=rec.download_count + 1))
    await db.commit()

    s3 = S3Client()
    url = s3.generate_presigned_url(rec.s3_key, expires_seconds=60)
    return RedirectResponse(url=url, status_code=307)


@router.get("/", response_model=Page[FileOut])
async def list_files(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    q: Optional[str] = Query(None, description="Поиск по имени файла"),
    visibility: Optional[VisibilityIn] = Query(None),
    owner_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    ext: Optional[str] = Query(None, description="Расширение без точки, напр. pdf"),
    order: str = Query("desc", regex="^(asc|desc)$"),
):
    query = select(File)
    vf = _visibility_filter(current_user)
    if vf is not True:
        query = query.where(vf)

    if q:
        query = query.where(File.filename_original.ilike(f"%{q}%"))
    if visibility:
        query = query.where(File.visibility == Visibility(visibility.value))
    if owner_id:
        query = query.where(File.owner_id == owner_id)
    if ext:
        query = query.where(File.ext.ilike(ext.lower()))
    if department_id is not None:
        # Только MANAGER/ADMIN могут фильтровать произвольный отдел.
        if current_user.role in (UserRole.ADMIN, UserRole.MANAGER):
            query = query.where(File.department_id == department_id)
        else:
            # USER игнорируем чужие отделы: применим только свой.
            query = query.where(File.department_id == current_user.department_id)

    query = query.order_by(File.id.asc() if order == "asc" else File.id.desc())
    rows = (await db.scalars(query)).all()

    items = [
        FileOut(
            id=r.id,
            filename_original=r.filename_original,
            visibility=r.visibility.value,
            status=r.status.value,
            size_bytes=r.size_bytes,
            mime_type=r.mime_type,
            ext=r.ext,
            download_count=r.download_count,
            metadata=r.metadata,
        )
        for r in rows
    ]
    return paginate(items)


@router.delete("/{file_id}", status_code=204)
async def delete_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rec = await db.scalar(select(File).where(File.id == file_id))
    if not rec:
        raise HTTPException(status_code=404, detail="File not found")

    _ensure_delete_access(current_user, rec)

    # удаление из S3 и БД
    s3 = S3Client()
    try:
        s3.delete_object(rec.s3_key)
    except Exception:
        # если объект уже нет в S3 — удаляем запись в БД всё равно
        pass

    await db.execute(delete(File).where(File.id == file_id))
    await db.commit()
    return
