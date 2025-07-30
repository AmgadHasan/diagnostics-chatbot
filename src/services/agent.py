from __future__ import annotations as _annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
)

from ..schemas.document import DocumentType
from .ingest import (
    document_ingestion_service_a,
    document_ingestion_service_b,
)

# Initialize the AI agent
agent = Agent(
    "openai:DeepSeek-V3-0324",
    tools=[
        document_ingestion_service_a.retrieve_chunks,
        document_ingestion_service_a.ingest_file,
    ],
)

# File tracking dictionary
uploaded_files: Dict[str, Dict[str, Any]] = {}

# Path for storing chat messages
MESSAGES_FILE = Path(__file__).parent.parent.parent / "chat_messages.json"


class JSONStorage:
    """Handles JSON file storage for chat messages."""

    def __init__(self):
        self.messages_file = MESSAGES_FILE
        # Create file if it doesn't exist
        if not self.messages_file.exists():
            self.messages_file.write_text('{"conversations": {}}')

    async def _load_messages(self) -> Dict[str, Any]:
        """Load messages from JSON file."""
        try:
            with open(self.messages_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # If file is corrupted or doesn't exist, reset it
            with open(self.messages_file, "w") as f:
                default_data = {"conversations": {}}
                json.dump(default_data, f)
            return default_data

    async def _save_messages(self, data: Dict[str, Any]):
        """Save messages to JSON file."""
        with open(self.messages_file, "w") as f:
            json.dump(data, f, indent=2)

    async def add_messages(self, messages: bytes, conversation_id: int = 1):
        """Add messages to storage as a single JSON object per conversation."""
        data = await self._load_messages()
        messages_str = messages.decode("utf-8")

        # Store or update conversation
        data["conversations"][str(conversation_id)] = {
            "messages": messages_str,
            "updated_at": datetime.now(tz=timezone.utc).isoformat(),
        }

        await self._save_messages(data)

    async def get_messages(self, conversation_id: int = 1) -> list[ModelMessage]:
        """Retrieve messages for a conversation from storage."""
        data = await self._load_messages()
        conv_data = data["conversations"].get(str(conversation_id))

        if conv_data and "messages" in conv_data:
            return ModelMessagesTypeAdapter.validate_json(conv_data["messages"])
        return []

    async def clear_chat_messages(self, conversation_id: int = 1):
        """Clear all chat messages for a conversation."""
        data = await self._load_messages()
        if str(conversation_id) in data["conversations"]:
            del data["conversations"][str(conversation_id)]
            await self._save_messages(data)


# Document ingestion tools for the agent
async def ingest_document_a(file_path: str, doc_type: str) -> str:
    """Tool for agent to ingest documents using service A."""
    try:
        doc_type_enum = DocumentType(doc_type)
        await document_ingestion_service_a.ingest_file(file_path, doc_type_enum)
        return f"Document {file_path} ingested successfully using service A"
    except Exception as e:
        return f"Error ingesting document: {str(e)}"


async def ingest_document_b(file_path: str, doc_type: str) -> str:
    """Tool for agent to ingest documents using service B."""
    try:
        doc_type_enum = DocumentType(doc_type)
        await document_ingestion_service_b.ingest_file(file_path, doc_type_enum)
        return f"Document {file_path} ingested successfully using service B"
    except Exception as e:
        return f"Error ingesting document: {str(e)}"


async def retrieve_documents_a(query: str, k: int = 10) -> List[Dict[str, Any]]:
    """Tool for agent to retrieve documents using service A."""
    try:
        results = await document_ingestion_service_a.retrieve_chunks(query, k)
        return [
            {"content": doc.page_content, "metadata": doc.metadata} for doc in results
        ]
    except Exception as e:
        return [{"error": f"Error retrieving documents: {str(e)}"}]


async def retrieve_documents_b(query: str, k: int = 10) -> List[Dict[str, Any]]:
    """Tool for agent to retrieve documents using service B."""
    try:
        results = await document_ingestion_service_b.retrieve_chunks(query, k)
        return [
            {"content": doc.page_content, "metadata": doc.metadata} for doc in results
        ]
    except Exception as e:
        return [{"error": f"Error retrieving documents: {str(e)}"}]


async def process_chat_message(message: str, storage: JSONStorage) -> str:
    """Process a chat message and return AI response."""
    # Get chat history
    messages = await storage.get_messages()

    # Run the agent with the user prompt and chat history
    result = await agent.run(message, message_history=messages)

    # Add new messages to storage
    await storage.add_messages(result.new_messages_json())

    # Return response
    return result.data


async def get_chat_history(storage: JSONStorage) -> list[ModelMessage]:
    """Retrieve chat history from storage."""
    return await storage.get_messages()


def register_uploaded_file(
    file_id: str,
    filename: str,
    content_type: DocumentType,
    size: int,
    file_path: str,
    description: Optional[str] = None,
):
    """Register an uploaded file in the tracking dictionary."""
    uploaded_files[file_id] = {
        "filename": filename,
        "content_type": content_type,
        "size": size,
        "description": description,
        "upload_timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "file_path": file_path,
    }


def get_uploaded_files() -> Dict[str, Dict[str, Any]]:
    """Get all uploaded files metadata."""
    return uploaded_files


def get_file_metadata(file_id: str) -> Optional[Dict[str, Any]]:
    """Get specific file metadata."""
    return uploaded_files.get(file_id)


async def query_documents(query: str, k: int = 10) -> List[Dict[str, Any]]:
    """Query documents using both ingestion services."""
    # Query both services
    results_a = await retrieve_documents_a(query, k)
    results_b = await retrieve_documents_b(query, k)

    # Combine results
    return results_a + results_b
