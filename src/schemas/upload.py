from pydantic import BaseModel
from .document import DocumentType


class UploadResponse(BaseModel):
    id: str
    filename: str
    content_type: DocumentType
    size: int
    message: str
