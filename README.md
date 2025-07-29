# diagnostics-chatbot

### Architecture Overview

┌───────────────────────────────────────────────────────────────────────────────┐
│                                Web Interface                                 │
│  (React/Streamlit) - handles chat UI and document uploads                 │
└───────────────────────┬───────────────────────────────────┬─────────────────┘
                        │                                   │
                        │ HTTP/WebSocket                    │ HTTP/WebSocket
                        ▼                                   ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                                API Layer                                      │
│  FastAPI (Python) - routes, auth, request validation (Pydantic models)       │
└───────────────────────┬───────────────────────────────────┬─────────────────┘
                        │                                   │
                        │                                   │
┌───────────────────────▼───────┐             ┌─────────────▼─────────────────┐
│        Document Ingestion     │             │        Chat Processing        │
│ - File upload processing      │             │ - Question analysis           │
│ - Web retrieval automation    │             │ - Context retrieval           │
│ - Pipeline management         │             │ - Response generation         │
└───────────────┬───────────────┘             └───────────────┬───────────────┘
                │                                             │
                │                                             │
┌───────────────▼───────┐                         ┌───────────▼───────────────┐
│   Dual Pipeline System                          │   LLM Integration         │
│ - Pipeline A:                                    │ - OpenAI/Anthropic/Gemini │
│   RecursiveTextSplitter → text-embedding-3-large│ - Response formatting     │
│   → pgvector                                     │ - Citation generation     │
│                                                 │                           │
│ - Pipeline B:                                    └───────────────────────────┘
│   SemanticSectionSplitter → all-MiniLM-L12-v2   │
│   → Pinecone                                    │
└────────────────────────────────────────────────┘
```mermaid
flowchart TD
    subgraph Web_Interface["Web Interface (React/Streamlit)"]
        A[Chat UI]
        B[Document Uploads]
    end

    subgraph API_Layer["API Layer (FastAPI)"]
        C[Routes]
        D[Auth]
        E[Validation]
    end

    subgraph Document_Ingestion
        F[File Processing]
        G[Web Retrieval]
        H[Pipeline Management]
    end

    subgraph Chat_Processing
        I[Question Analysis]
        J[Context Retrieval]
        K[Response Generation]
    end

    subgraph Dual_Pipeline
        subgraph Pipeline_A["Pipeline A"]
            L[RecursiveTextSplitter]
            M[text-embedding-3-large]
            N[pgvector]
        end
        subgraph Pipeline_B["Pipeline B"]
            O[SemanticSectionSplitter]
            P[all-MiniLM-L12-v2]
            Q[Pinecone]
        end
    end

    subgraph LLM_Integration
        R[OpenAI/Anthropic/Gemini]
        S[Response Formatting]
        T[Citation Generation]
    end

    Web_Interface -->|HTTP/WebSocket| API_Layer
    API_Layer -->|HTTP/WebSocket| Document_Ingestion
    API_Layer -->|HTTP/WebSocket| Chat_Processing
    Document_Ingestion --> Dual_Pipeline
    Chat_Processing --> LLM_Integration
```

### Subtask Breakdown

#### 1. Core Infrastructure Setup
- [ ] Set up FastAPI application skeleton with proper routing
- [ ] Configure Pydantic models for:
  - Document upload requests
  - Chat messages
  - Pipeline configuration
- [ ] Implement basic auth/rate limiting
- [ ] Set up logging and monitoring

#### 2. Document Ingestion System
- [ ] Implement file upload handler (PDF/DOCX parsing)
- [ ] Design web retrieval automation:
  - Manufacturer/model detection from chat context
  - Web search integration (SerpAPI/Google Search API)
  - PDF/HTML download and extraction
- [ ] Create document preprocessing utilities

#### 3. Dual Pipeline Implementation
- [ ] Pipeline A:
  - RecursiveTextSplitter configuration (optimal chunk size/overlap)
  - text-embedding-3-large integration
  - pgvector database setup and CRUD operations
- [ ] Pipeline B:
  - SemanticSectionSplitter implementation
  - all-MiniLM-L12-v2 embedding model
  - Pinecone integration
- [ ] Pipeline selection/routing logic

#### 4. Chat Processing System
- [ ] Question analysis module:
  - Intent detection
  - Entity extraction (for troubleshooting context)
- [ ] Context retrieval:
  - Hybrid search strategy
  - Pipeline selection logic
- [ ] Response generation:
  - LLM API integration (OpenAI/Anthropic/Gemini)
  - Citation formatting (doc name + page/URL)

#### 5. Web Interface
- [ ] Choose and implement UI framework (React/Streamlit/Gradio)
- [ ] Design chat interface components
- [ ] Implement document upload UI
- [ ] Set up WebSocket/REST API communication

#### 6. Deployment & Documentation
- [ ] Dockerize application
- [ ] Create docker-compose.yml with all dependencies
- [ ] Write comprehensive README.md
- [ ] Create architecture diagram
- [ ] Document pipeline configurations and rationale
