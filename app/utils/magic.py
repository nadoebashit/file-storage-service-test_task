import magic

# Mapping допустимых MIME для расширений
ALLOWED_EXT_MIME = {
    "pdf": {"application/pdf"},
    "docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        # некоторые либы определяют docx как zip:
        "application/zip",
    },
    "doc": {"application/msword", "application/x-msword"},
}

def sniff_mime(data: bytes) -> str:
    return magic.from_buffer(data, mime=True)

def ensure_mime_matches_ext(ext: str, detected_mime: str) -> bool:
    ext = ext.lower().lstrip(".")
    allowed = ALLOWED_EXT_MIME.get(ext, set())
    return detected_mime in allowed
