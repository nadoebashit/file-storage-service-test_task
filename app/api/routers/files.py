import asyncio
import mimetypes
from uuid import uuid4
from fastapi import APIRouter, Depends, File as FileUpload, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from fastapi_pagination import Page, add_pagination, paginate

from app.core.deps import get_current_user, get_db
from app.db.models.user import User
from app.db.models.file import File
from app.db.models.enums import Visibility, FileStatus, UserRole
from app.schemas.file import UploadResponse, FileOut, VisibilityIn
from app.services.storage_s3 import S3Client
from app.tasks.metadata import extract_metadata_for_file
from app.utils.validators import ensure_upload_allowed

router = APIRouter()

def _visibility_filter(user: User):
    if user.role in (UserRole.ADMIN, UserRole.MANAGER):
        return True
    return or_(
        File.owner_id == user.id,
        File.visibility == Visibility.PUBLIC,
        and_(File.visibility == Visibility.DEPARTMENT, File.department_id == user.department_id),
    )

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    visibility: VisibilityIn = Form(...),
    file: UploadFile = FileUpload(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # определить ext/mime/size
    filename = file.filename or "upload.bin"
    ext = (filename.split(".")[-1]).lower() if "." in filename else ""
    content = await file.read()
    size = len(content)
    mime = file.content_type or (mimetypes.guess_type(filename)[0] or "application/octet-stream")

    # валидации по роли
    final_visibility = ensure_upload_allowed(current_user.role.value, ext, size, visibility.value)

    # S3 key
    s3_key = f"{current_user.department_id}/{current_user.id}/{uuid4()}.{ext}"
    s3 = S3Client()
    from io import BytesIO
    s3.upload_fileobj(s3_key, BytesIO(content))

    # create DB row
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

    # запустить извлечение метаданных в фоне
    asyncio.create_task(extract_metadata_for_file(rec.id))

    return UploadResponse(file=FileOut(
        id=rec.id,
        filename_original=rec.filename_original,
        visibility=rec.visibility.value,
        status=rec.status.value,
        size_bytes=rec.size_bytes,
        mime_type=rec.mime_type,
        ext=rec.ext,
        download_count=rec.download_count,
        metadata=rec.metadata,
    ))

@router.get("/{file_id}", response_model=FileOut)
async def get_file_info(file_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    rec = await db.scalar(select(File).where(File.id == file_id))
    if not rec:
        raise HTTPException(status_code=404, detail="File not found")
    # проверка доступа на чтение
    if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):
        allowed = (
            rec.owner_id == current_user.id or
            rec.visibility == Visibility.PUBLIC or
            (rec.visibility == Visibility.DEPARTMENT and rec.department_id == current_user.department_id)
        )
        if not allowed:
            raise HTTPException(status_code=403, detail="Forbidden")
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
async def download_file(file_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from sqlalchemy import update
    rec = await db.scalar(select(File).where(File.id == file_id))
    if not rec:
        raise HTTPException(status_code=404, detail="File not found")
    # проверка доступа
    if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):
        allowed = (
            rec.owner_id == current_user.id or
            rec.visibility == Visibility.PUBLIC or
            (rec.visibility == Visibility.DEPARTMENT and rec.department_id == current_user.department_id)
        )
        if not allowed:
            raise HTTPException(status_code=403, detail="Forbidden")

    # инкремент счётчика
    await db.execute(update(File).where(File.id == file_id).values(download_count=rec.download_count + 1))
    await db.commit()

    # presigned url
    s3 = S3Client()
    url = s3.generate_presigned_url(rec.s3_key, expires_seconds=60)
    return {"url": url, "expires_in": 60}

@router.get("/", response_model=Page[FileOut])
async def list_files(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = select(File)
    vf = _visibility_filter(current_user)
    if vf is not True:
        q = q.where(vf)
    res = (await db.scalars(q.order_by(File.id.desc()))).all()
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
        for r in res
    ]
    return paginate(items)
