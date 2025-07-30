from typing import Optional
from pydantic import BaseModel
from .document import DocumentType


class FileMetadata(BaseModel):
    id: str
    filename: str
    content_type: DocumentType
    size: int
    description: Optional[str] = None
    upload_timestamp: str
    file_path: str


class FileListResponse(BaseModel):
    files: list[FileMetadata]
