from typing import List
from pydantic import BaseModel
from langchain.schema import Document


class QueryRequest(BaseModel):
    query: str
    k: int = 10


class QueryResponse(BaseModel):
    results: List[Document]
