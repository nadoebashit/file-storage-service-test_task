import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.db.session import async_session_maker
from app.db.models.file import File
from app.db.models.enums import FileStatus
from app.services.storage_s3 import S3Client
from app.services.metadata import extract_pdf_meta, extract_docx_meta,extract_doc_meta
from app.tasks.celery_app import celery


async def _extract_metadata_for_file(file_id: int):
    async with async_session_maker() as session:
        file = await session.scalar(select(File).where(File.id == file_id))
        if not file:
            return
        s3 = S3Client()
        blob = s3.download_to_bytes(file.s3_key)
        meta = {}
        try:
            if file.ext.lower() == "pdf":
                meta = extract_pdf_meta(blob)
            elif file.ext.lower() == "docx":
                meta = extract_docx_meta(blob)
            elif file.ext.lower() == "doc":
                meta = extract_doc_meta(blob)    
            else:
                meta = {"note": "DOC basic support (best-effort)"}
            await session.execute(
                update(File).where(File.id == file_id).values(metadata=meta, status=FileStatus.READY)
            )
            await session.commit()
        except Exception:
            await session.execute(
                update(File).where(File.id == file_id).values(status=FileStatus.FAILED)
            )
            await session.commit()


@celery.task(name="extract_metadata")
def extract_metadata_task(file_id: int):
    # Оборачиваем async-функцию для выполнения в Celery
    asyncio.run(_extract_metadata_for_file(file_id))
