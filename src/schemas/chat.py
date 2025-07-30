from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    timestamp: str


class ChatMessage(BaseModel):
    role: str
    timestamp: str
    content: str
