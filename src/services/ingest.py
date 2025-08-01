import os
from pathlib import Path
from typing import List

from langchain.schema import Document
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_nvidia import NVIDIAEmbeddings
from langchain_openai import AzureOpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from ..schemas.document import DocumentType
from ..services.utils import generate_file_description

# Initialize clients and embeddings once for each pipeline
# Pipeline A (Qdrant + Azure OpenAI A)
embeddings_a = AzureOpenAIEmbeddings(
    model=os.environ.get("EMBEDDING_A_MODEL"),
    azure_endpoint=os.environ.get("EMBEDDING_A_API_BASE"),
    api_version=os.environ.get("EMBEDDING_A_API_VERSION"),
    api_key=os.environ.get("EMBEDDING_A_API_KEY"),
)

client_a = QdrantClient(
    url=os.environ.get("QDRANT_URL"),
    api_key=os.environ.get("QDRANT_API_KEY"),
    https=True,
    port=443,
)

# Pipeline B (PGVector + Azure OpenAI B)
embeddings_b = NVIDIAEmbeddings(
    model=os.environ.get("EMBEDDING_B_MODEL"),
    base_url=os.environ.get("EMBEDDING_B_API_BASE"),
    api_key=os.environ.get("EMBEDDING_B_API_KEY"),
)

# Initialize Qdrant collection once
try:
    client_a.create_collection(
        collection_name="demo_collection",
        vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
    )
except Exception:
    pass  # Collection already exists


# Shared utility functions
async def load_pdf_pages(file_path: str | Path) -> List[Document]:
    """
    Load pages from a PDF file asynchronously.

    Args:
        file_path: Path to the PDF file

    Returns:
        List of loaded document pages
    """
    loader = PyPDFLoader(str(file_path))
    pages: List[Document] = []
    async for page in loader.alazy_load():
        pages.append(page)
    return pages


async def load_docx_pages(file_path: str | Path) -> List[Document]:
    """
    Load pages from a DOCX file.

    Args:
        file_path: Path to the DOCX file

    Returns:
        List of loaded document pages
    """
    loader = Docx2txtLoader(str(file_path))
    return loader.load()


# Pipeline A (Qdrant) implementation
async def _ingest_with_pipeline_a(
    file_path: str | Path, document_type: DocumentType
) -> str:
    """
    Process document using pipeline A: RecursiveCharacterTextSplitter, Qdrant vectorstore with Azure OpenAI embeddings A.

    Args:
        file_path: Path to the document file to process
        document_type: Type of document (PDF or DOCX)

    Returns:
        str: Generated file description
    """
    # Use shared vector store instance for pipeline A
    vectorstore_a = QdrantVectorStore(
        client=client_a,
        collection_name="demo_collection",
        embedding=embeddings_a,
    )

    # Load document based on type
    if document_type == DocumentType.PDF:
        pages = await load_pdf_pages(file_path)
    elif document_type == DocumentType.DOCX:
        pages = await load_docx_pages(file_path)
    else:
        raise ValueError(f"Unsupported document type: {document_type}")

    # Split documents
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=750, chunk_overlap=100)
    texts = text_splitter.split_documents(pages)

    # Process documents in batches
    batch_size = 16
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        vectorstore_a.add_documents(documents=batch)

    # Generate description
    description = await generate_file_description(
        "\n".join([p.page_content for p in pages])
    )
    return description


async def _retrieve_from_pipeline_a(query: str, k: int = 10) -> List[Document]:
    """
    Retrieve chunks from pipeline A.

    Args:
        query: Search query string
        k: Number of similar chunks to retrieve

    Returns:
        List of matching document chunks
    """
    # Use shared vector store instance for pipeline A
    vectorstore_a = QdrantVectorStore(
        client=client_a,
        collection_name="demo_collection",
        embedding=embeddings_a,
    )

    return vectorstore_a.similarity_search(query, k=k)


# Pipeline B (PGVector) implementation
async def _ingest_with_pipeline_b(
    file_path: str | Path, document_type: DocumentType
) -> List[Document]:
    """
    Process document using pipeline B: SemanticChunker, PGVector vectorstore with Azure OpenAI embeddings B.

    Args:
        file_path: Path to the document file to process
        document_type: Type of document (PDF or DOCX)

    Returns:
        List of loaded document pages
    """
    # Use shared vector store instance for pipeline B
    connection = os.environ.get("PG_VECTOR_CONNECTION")
    vectorstore_b = PGVector(
        embeddings=embeddings_b,
        collection_name="default_collection",
        connection=connection,
        use_jsonb=True,
    )

    # Load document based on type
    if document_type == DocumentType.PDF:
        pages = await load_pdf_pages(file_path)
    elif document_type == DocumentType.DOCX:
        pages = await load_docx_pages(file_path)
    else:
        raise ValueError(f"Unsupported document type: {document_type}")

    # Split documents using semantic chunker
    text_splitter = SemanticChunker(embeddings_b)
    texts = text_splitter.split_documents(pages)

    # Add documents to vector store
    vectorstore_b.add_documents(documents=texts)

    return pages


async def _retrieve_from_pipeline_b(query: str, k: int = 10) -> List[Document]:
    """
    Retrieve chunks from Pipeline B.

    Args:
        query: Search query string
        k: Number of similar chunks to retrieve

    Returns:
        List of matching document chunks
    """
    # Use shared vector store instance for pipeline B
    connection = os.environ.get("PG_VECTOR_CONNECTION")
    vectorstore_b = PGVector(
        embeddings=embeddings_b,
        collection_name="default_collection",
        connection=connection,
        use_jsonb=True,
    )

    return vectorstore_b.similarity_search(query, k=k)


# Main interface functions
async def ingest_file(
    file_path: str | Path, document_type: DocumentType, pipeline: str = "A"
) -> str:
    """
    Ingest a document file (PDF or DOCX) using one of the available document processing pipelines.
    The available pipelines are:
    - A: Splits the document into chunks using RecursiveCharacterTextSplitter.
    - B: Splits the document into chunks using SemanticChunker.

    Args:
        file_path: Path to the document file to process. Can be a local path or a web url
        document_type: Type of document (one of "pdf" or "docx")
        pipeline: Which pipeline to use ("A" for Qdrant, "B" for PGVector)

    Returns:
        str: Generated file description (for pipeline A) or empty string (for pipeline B)

    Raises:
        ValueError: If unsupported document type or invalid pipeline
    """
    if pipeline == "A":
        return await _ingest_with_pipeline_a(file_path, document_type)
    elif pipeline == "B":
        await _ingest_with_pipeline_b(file_path, document_type)
        return ""
    else:
        raise ValueError(f"Invalid pipeline: {pipeline}. Use 'A' or 'B'.")


async def search_knowledge_base(query: str, k: int = 10) -> List[Document]:
    """
    Search the internal knowledge base using a query.

    Args:
        query: Search query string
        k: Number of similar chunks to retrieve

    Returns:
        List of matching document chunks

    Raises:
        ValueError: If invalid pipeline
    """
    results_a = await _retrieve_from_pipeline_a(query, k)
    results_b = await _retrieve_from_pipeline_b(query, k)
    return results_a + results_b
