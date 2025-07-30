import os
from pathlib import Path
from typing import List

from langchain.schema import Document
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import AzureOpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from ..schemas.document import DocumentType


def get_qdrant_client() -> QdrantClient:
    """
    Initialize and return a Qdrant client using provided configuration from environment variables.

    Returns:
        QdrantClient: An instance of QdrantClient connected to the specified Qdrant server.
    """
    client = QdrantClient(
        url=os.environ.get("QDRANT_URL"), api_key=os.environ.get("QDRANT_API_KEY")
    )
    return client


class DocumentIngestionServiceA:
    def __init__(self, collection_name: str = "default_collection"):
        self.embeddings = AzureOpenAIEmbeddings(
            model=os.environ.get("EMBEDDING_A_MODEL"),
            azure_endpoint=os.environ.get("EMBEDDING_A_API_BASE"),
            api_version=os.environ.get("EMBEDDING_A_API_VERSION"),
            api_key=os.environ.get("EMBEDDING_A_API_KEY"),
        )
        self.collection_name = collection_name
        self.client: QdrantClient = get_qdrant_client()
        try:
            self.client.create_collection(
                collection_name="demo_collection",
                vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
            )
        except Exception as e:
            print(e)
            pass
        # Create vector store
        self.vectorstore = QdrantVectorStore(
            client=self.client,
            collection_name="demo_collection",
            embedding=self.embeddings,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=750, chunk_overlap=100
        )

    async def _load_pdf_pages(self, file_path: str | Path) -> List[Document]:
        """Load pages from a PDF file asynchronously.

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

    async def _load_docx_pages(self, file_path: str | Path) -> List[Document]:
        """Load pages from a DOCX file.

        Args:
            file_path: Path to the DOCX file

        Returns:
            List of loaded document pages
        """
        loader = Docx2txtLoader(str(file_path))
        return loader.load()

    async def ingest_file(self, file_path: str | Path, type: DocumentType):
        """Process a PDF file into a Qdrant vector store.

        Args:
            file_path: Path to the PDF file to process

        Returns:
            None
        """
        if type == DocumentType.PDF:
            pages = await self._load_pdf_pages(file_path)
        elif type == DocumentType.DOCX:
            pages = await self._load_docx_pages(file_path)
        else:
            raise ValueError(f"Unsupported document type: {type}")

        texts = self.text_splitter.split_documents(pages)

        self.vectorstore.add_documents(documents=texts)

        self.retriever = self.vectorstore.as_retriever()

    async def retrieve_chunks(self, query: str, k: int = 10) -> List[Document]:
        """Retrieve similar document chunks from the vector store.

        Args:
            query: Search query string
            k: Number of similar chunks to retrieve

        Returns:
            List of matching document chunks
        """
        if not self.vectorstore:
            raise ValueError(
                "Vector store not initialized. Call ingest_pdf_file first."
            )

        return self.vectorstore.similarity_search(query, k=k)


class DocumentIngestionServiceB:
    def __init__(self, collection_name: str = "default_collection"):
        self.embeddings = AzureOpenAIEmbeddings(
            model=os.environ.get("EMBEDDING_B_MODEL"),
            azure_endpoint=os.environ.get("EMBEDDING_B_API_BASE"),
            api_version=os.environ.get("EMBEDDING_B_API_VERSION"),
            api_key=os.environ.get("EMBEDDING_B_API_KEY"),
        )

        self.collection_name = collection_name
        self.connection = os.environ.get("PG_VECTOR_CONNECTION")
        try:
            self.client.create_collection(
                collection_name="demo_collection",
                vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
            )
        except Exception as e:
            print(e)
            pass
        # Create vector store
        self.vectorstore = PGVector(
            embeddings=self.embeddings,
            collection_name=self.collection_name,
            connection=self.connection,
            use_jsonb=True,
        )
        self.text_splitter = SemanticChunker(self.embeddings)

    async def _load_pdf_pages(self, file_path: str | Path) -> List[Document]:
        """Load pages from a PDF file asynchronously.

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

    async def _load_docx_pages(self, file_path: str | Path) -> List[Document]:
        """Load pages from a DOCX file.

        Args:
            file_path: Path to the DOCX file

        Returns:
            List of loaded document pages
        """
        loader = Docx2txtLoader(str(file_path))
        return loader.load()

    async def ingest_pdf_file(self, file_path: str | Path, type: DocumentType):
        """Process a PDF file into a Qdrant vector store.

        Args:
            file_path: Path to the PDF file to process

        Returns:
            None
        """
        if type == DocumentType.PDF:
            pages = await self._load_pdf_pages(file_path)
        elif type == DocumentType.DOCX:
            pages = await self._load_docx_pages(file_path)
        else:
            raise ValueError(f"Unsupported document type: {type}")

        texts = self.text_splitter.split_documents(pages)

        self.vectorstore.add_documents(documents=texts)

        self.retriever = self.vectorstore.as_retriever()

    async def retrieve_chunks(self, query: str, k: int = 2) -> List[Document]:
        """Retrieve similar document chunks from the vector store.

        Args:
            query: Search query string
            k: Number of similar chunks to retrieve

        Returns:
            List of matching document chunks
        """
        if not self.vectorstore:
            raise ValueError(
                "Vector store not initialized. Call ingest_pdf_file first."
            )

        return self.vectorstore.similarity_search(query, k=k)


document_ingestion_service_a = DocumentIngestionServiceA()
document_ingestion_service_b = DocumentIngestionServiceA()
