from pathlib import Path

import aiofiles
from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel

from .schemas.document import DocumentType
from .services.ingest import document_ingestion_service_a

app = FastAPI()


class UploadResponse(BaseModel):
    id: str
    filename: str
    content_type: DocumentType
    size: int
    message: str


@app.post("/upload/")
async def upload_document(file: UploadFile, type: DocumentType) -> UploadResponse:
    try:
        if type not in [DocumentType.PDF, DocumentType.DOCX]:
            raise HTTPException(
                status_code=400, detail="Only PDF and DOCX files are allowed"
            )

        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        file_path = upload_dir / file.filename

        # Use aiofiles for async file operations
        async with aiofiles.open(file_path, "wb") as buffer:
            # Read chunks to handle large files efficiently
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                await buffer.write(chunk)

        await document_ingestion_service_a.ingest_file(file_path=file_path, type=type)

        return UploadResponse(
            id="some-string",
            filename=file.filename,
            content_type=file.content_type,
            size=file_path.stat().st_size,
            message="File uploaded successfully",
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Error uploading document")


class StatusResponse(BaseModel):
    status: str
    version: str


@app.get("/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    return StatusResponse(status="OK", version="1.0.0")
