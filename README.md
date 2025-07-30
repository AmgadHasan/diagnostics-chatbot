# diagnostics-chatbot

### Todos
1. Add logic to handle multple users (use chat threads with unique IDs)
2. Link documents to threads/users (currently all documents and their chunks can be accessed all the time)
3. Improve error handling
4. Write tests


### Architecture Overview

```mermaid
flowchart TD
    subgraph Web_Interface["Web Interface (React/Streamlit)"]
        A[Chat UI]
        B[Document Uploads]
    end

    subgraph API_Layer["API Layer (FastAPI)"]
        C[Routes]
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
    Dual_Pipeline --> Chat_Processing
    Chat_Processing --> LLM_Integration
```

### Subtask Breakdown

#### 1. Core Infrastructure Setup
- [ ] Set up FastAPI application skeleton with proper routing
- [ ] Configure Pydantic models for:
  - Document upload requests
  - Chat messages


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

#### Extras (to be done later)
- [ ] Implement basic auth/rate limiting
- [ ] Set up logging and monitoring