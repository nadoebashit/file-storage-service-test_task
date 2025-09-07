from datetime import datetime
from typing import Any
from pypdf import PdfReader
from docx import Document
from io import BytesIO
import tempfile
import re
import os
import textract

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


def extract_doc_meta(data: bytes) -> dict[str, object]:
    """
    Best-effort для .doc:
      - получаем чистый текст через textract (antiword/catdoc)
      - считаем параграфы как блоки по пустым строкам
      - оцениваем 'таблицы' эвристикой: линии с >=2 табами
      - title/author/created не всегда доступны стабильно — вернём пустые строки
    """
    # Пишем во временный .doc, textract работает по имени файла
    with tempfile.NamedTemporaryFile(suffix=".doc", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        raw = textract.process(tmp_path)  # bytes
        text = raw.decode("utf-8", errors="ignore")
        # параграфы: непустые блоки, разделённые \n\n
        blocks = [b for b in re.split(r"\n\s*\n", text) if b.strip()]
        paragraphs = len(blocks)

        # 'таблицы': строки с >=2 '\t' (очень грубо, но для тестового ок)
        tables = sum(1 for line in text.splitlines() if line.count("\t") >= 2)

        return {
            "paragraphs": paragraphs,
            "tables": tables,
            "title": "",
            "author": "",
            "created": "",
        }
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass