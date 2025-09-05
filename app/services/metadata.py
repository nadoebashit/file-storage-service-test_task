from datetime import datetime
from typing import Any
from pypdf import PdfReader
from docx import Document

def extract_pdf_meta(data: bytes) -> dict[str, Any]:
    from io import BytesIO
    reader = PdfReader(BytesIO(data))
    info = reader.metadata or {}
    return {
        "pages": len(reader.pages),
        "author": str(info.get("/Author") or ""),
        "title": str(info.get("/Title") or ""),
        "creation_date": str(info.get("/CreationDate") or ""),
        "creator": str(info.get("/Creator") or ""),
        "producer": str(info.get("/Producer") or ""),
    }

def extract_docx_meta(data: bytes) -> dict[str, Any]:
    from io import BytesIO
    doc = Document(BytesIO(data))
    cp = doc.core_properties
    return {
        "paragraphs": sum(len(p.text) > 0 for p in doc.paragraphs),
        "tables": len(doc.tables),
        "title": cp.title or "",
        "author": cp.author or "",
        "created": str(cp.created or ""),
    }
