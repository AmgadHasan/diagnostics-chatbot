import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from openai import AsyncOpenAI
from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
)

from ..schemas.document import DocumentType

client = AsyncOpenAI()
DATA_DIR = Path(__file__).parent.parent.parent

MESSAGES_FILE = DATA_DIR / "chat_messages.json"

UPLOADED_FILES_FILE = DATA_DIR / "uploaded_files.json"

# File tracking dictionary (loaded from file)
uploaded_files: Dict[str, Dict[str, Any]] = {}


def register_uploaded_file(
    file_id: str,
    filename: str,
    content_type: DocumentType,
    size: int,
    file_path: str,
    description: Optional[str] = None,
    content: Optional[str] = None,
):
    """Register an uploaded file in the tracking dictionary.

    Args:
        file_id: Unique file ID
        filename: Original filename
        content_type: Document type
        size: File size in bytes
        file_path: Path to stored file
        description: Optional manual description
        content: Optional file content for auto-description
    """
    if description is None and content:
        description = asyncio.run(generate_file_description(content))

    file_data = {
        "filename": filename,
        "content_type": content_type,
        "size": size,
        "description": description,
        "upload_timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "file_path": file_path,
    }
    uploaded_files[file_id] = file_data
    _save_uploaded_files(uploaded_files)


def get_uploaded_files() -> Dict[str, Dict[str, Any]]:
    """Get all uploaded files metadata."""
    return uploaded_files


def get_file_metadata(file_id: str) -> Optional[Dict[str, Any]]:
    """Get specific file metadata."""
    return uploaded_files.get(file_id)


def _load_uploaded_files() -> Dict[str, Dict[str, Any]]:
    """Load uploaded files metadata from file."""
    try:
        with open(UPLOADED_FILES_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # If file is corrupted or doesn't exist, return empty dict
        return {}


def _save_uploaded_files(data: Dict[str, Dict[str, Any]]):
    """Save uploaded files metadata to file."""
    with open(UPLOADED_FILES_FILE, "w") as f:
        json.dump(data, f, indent=2)


# Initialize uploaded_files from disk
uploaded_files = _load_uploaded_files()


async def generate_file_description(content: str) -> Optional[str]:
    """Generate a description for file content using OpenAI.
    Args:
        content: The file content to generate description for (first 1000 words used)

    Returns:
        Generated description or None if generation fails
    """
    try:
        # Get first 1000 words
        words = content.split()[:1000]
        truncated_content = " ".join(words)

        # Use OpenAI to generate description
        response = await client.chat.completions.create(
            model=os.environ.get("LLM_MODEL"),
            messages=[
                {
                    "role": "system",
                    "content": "Generate a concise description of the provided file content. The description should be less than 100 words. Avoid using newlines.",
                },
                {
                    "role": "user",
                    "content": f"File content:\n{truncated_content}",
                },
            ],
            temperature=0.3,
            max_tokens=512,
        )
        return response.choices[0].message.content.strip() if response.choices else None
    except Exception:
        return None


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
