from pydantic import BaseModel
from enum import Enum

class VisibilityIn(str, Enum):
    private = "private"
    department = "department"
    public = "public"

class FileOut(BaseModel):
    id: int
    filename_original: str
    visibility: str
    status: str
    size_bytes: int
    mime_type: str
    ext: str
    download_count: int
    metadata: dict

class UploadResponse(BaseModel):
    file: FileOut
