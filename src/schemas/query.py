from typing import Any, List, Dict
from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    k: int = 10


class QueryResponse(BaseModel):
    results: List[Dict[str, Any]]
