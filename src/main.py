from __future__ import annotations as _annotations

import logging
import logging.handlers
import uuid
from pathlib import Path
from typing import List

import aiofiles
from fastapi import FastAPI, HTTPException, UploadFile, Response
from .services.agent import (
    JSONStorage,
    get_chat_history,
    get_file_metadata,
    get_uploaded_files,
    process_chat_message,
    query_documents,
    register_uploaded_file,
)
from fastapi.middleware.cors import CORSMiddleware

from .schemas.chat import ChatMessage, ChatRequest, ChatResponse
from .schemas.document import DocumentType
from .schemas.files import FileListResponse, FileMetadata
from .schemas.query import QueryRequest, QueryResponse
from .schemas.status import StatusResponse
from .schemas.upload import UploadResponse
from .services.ingest import document_ingestion_service_a

# Storage instance for application
storage = JSONStorage()

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "app.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting up application")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application")


@app.get("/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    """Get service status."""
    return StatusResponse(status="OK", version="1.0.0")


@app.post("/upload/", response_model=UploadResponse)
async def upload_document(file: UploadFile, type: DocumentType) -> UploadResponse:
    """Upload and ingest a document."""
    try:
        logger.info(f"Received upload request for file: {file.filename} (type: {type})")
        if type not in [DocumentType.PDF, DocumentType.DOCX]:
            logger.warning(f"Invalid file type attempted: {type}")
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

        # Ingest document using service A
        await document_ingestion_service_a.ingest_file(file_path=file_path, type=type)

        # Register file in tracking system
        file_id = str(uuid.uuid4())
        file_size = file_path.stat().st_size
        register_uploaded_file(
            file_id=file_id,
            filename=file.filename,
            content_type=type,
            size=file_size,
            file_path=str(file_path),
        )

        logger.info(f"Successfully uploaded file: {file.filename} (ID: {file_id})")
        return UploadResponse(
            id=file_id,
            filename=file.filename,
            content_type=type,
            size=file_size,
            message="File uploaded and ingested successfully",
        )
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error uploading document: {str(e)}"
        )


@app.post("/chat/", response_model=ChatResponse)
async def post_chat(request: ChatRequest) -> ChatResponse:
    """Process a chat message and return AI response."""
    try:
        logger.info(f"Processing message: {request.message}")
        response_text = await process_chat_message(request.message, storage)
        logger.info("Successfully processed chat message")
        from datetime import datetime, timezone

        return ChatResponse(
            response=response_text,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@app.get("/chat/", response_model=List[ChatMessage])
async def get_chat() -> List[ChatMessage]:
    """Retrieve chat history from JSON storage."""
    try:
        logger.info("Retrieving chat history")
        messages = await get_chat_history(storage)  # Returns all messages from JSON
        chat_messages = []

        from pydantic_ai.messages import (
            ModelRequest,
            ModelResponse,
            TextPart,
            UserPromptPart,
        )

        for m in messages:
            first_part = m.parts[0]
            if isinstance(m, ModelRequest):
                if isinstance(first_part, UserPromptPart):
                    assert isinstance(first_part.content, str)
                    chat_messages.append(
                        ChatMessage(
                            role="user",
                            timestamp=first_part.timestamp.isoformat(),
                            content=first_part.content,
                        )
                    )
            elif isinstance(m, ModelResponse):
                if isinstance(first_part, TextPart):
                    chat_messages.append(
                        ChatMessage(
                            role="model",
                            timestamp=m.timestamp.isoformat(),
                            content=first_part.content,
                        )
                    )

        return chat_messages
    except Exception as e:
        logger.error(f"Error retrieving chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving chat: {str(e)}")


@app.delete("/chat/", status_code=204)
async def clear_chat():
    """Clear all chat messages."""
    try:
        logger.info("Clearing all chat messages")
        await storage.clear_chat_messages()
        return Response(status_code=204)
    except Exception as e:
        logger.error(f"Error clearing chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error clearing chat: {str(e)}")


@app.get("/files/", response_model=FileListResponse)
async def get_files() -> FileListResponse:
    """List all uploaded files with metadata."""
    try:
        logger.info("Retrieving uploaded files list")
        files_data = get_uploaded_files()
        files = []
        for file_id, metadata in files_data.items():
            files.append(
                FileMetadata(
                    id=file_id,
                    filename=metadata["filename"],
                    content_type=metadata["content_type"],
                    size=metadata["size"],
                    description=metadata.get("description"),
                    upload_timestamp=metadata["upload_timestamp"],
                    file_path=metadata["file_path"],
                )
            )
        return FileListResponse(files=files)
    except Exception as e:
        logger.error(f"Error retrieving files: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving files: {str(e)}")


@app.get("/files/{file_id}", response_model=FileMetadata)
async def get_file(file_id: str) -> FileMetadata:
    """Get specific file metadata."""
    try:
        logger.info(f"Retrieving metadata for file ID: {file_id}")
        metadata = get_file_metadata(file_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="File not found")

        return FileMetadata(
            id=file_id,
            filename=metadata["filename"],
            content_type=metadata["content_type"],
            size=metadata["size"],
            description=metadata.get("description"),
            upload_timestamp=metadata["upload_timestamp"],
            file_path=metadata["file_path"],
        )
    except HTTPException:
        logger.warning(f"File not found: {file_id}")
        raise
    except Exception as e:
        logger.error(f"Error retrieving file metadata: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving file: {str(e)}")


@app.post("/query/", response_model=QueryResponse)
async def query_documents_endpoint(request: QueryRequest) -> QueryResponse:
    """Query documents using both ingestion services."""
    try:
        logger.info(f"Processing query: {request.query} (k={request.k})")
        results = await query_documents(request.query, request.k)
        logger.info(f"Query returned {len(results)} results")
        return QueryResponse(results=results)
    except Exception as e:
        logger.error(f"Error querying documents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error querying documents: {str(e)}"
        )
