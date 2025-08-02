# diagnostics-chatbot
## How to run
1. Create an `.env` file from the example env file:
```sh
cp .env.example .env
```
2. Plug in the needed values in the `.env` file (API keys, models, etc)

3. Start the docker compose:
```sh
docker compose up --build

# or use the bash script: `bash compose_up.sh`

```
4. The chat web ui will be available at http://localhost:3000/
![alt text](assets/image.png)

### Todos
1. Add logic to handle multple users (use chat threads with unique IDs)
2. Link documents to threads/users (currently all documents and their chunks can be accessed all the time)
3. Improve error handling
4. Write tests


### Architecture Overview

```mermaid
flowchart TD
    subgraph Frontend["Frontend (React)"]
        A[Chat Interface]
        B[Document Upload]
        C[File Management]
    end

    subgraph API_Layer["FastAPI Backend"]
        D[REST Endpoints]
        E[WebSocket Handler]
        F[File Upload Service]
    end

    subgraph Agent_Layer["Pydantic AI Agent"]
        G[Agent Orchestrator]
        H[Tool Registry]
        I[Context Manager]
    end

    subgraph Tools["Agent Tools"]
        J[Search Knowledge Base]
        K[Web Search<br/>DuckDuckGo]
        L[Ingest Document]
    end

    subgraph Dual_Pipeline["Dual Ingestion & Retrieval Pipeline"]
        subgraph Pipeline_A["Pipeline A - Qdrant"]
            M[RecursiveCharacterTextSplitter<br/>chunk_size=750, overlap=100]
            N[Azure OpenAI Embeddings]
            O[Qdrant Vector Store]
        end
        
        subgraph Pipeline_B["Pipeline B - PGVector"]
            P[SemanticChunker<br/>embedding-based]
            Q[Embeddings]
            R[PGVector<br/>PostgreSQL]
        end
    end

    subgraph LLM_Integration["LLM Integration"]
        S[OpenAI/Azure OpenAI Models]
        T[Response Generation]
        U[Citation & Formatting]
    end

    subgraph Observability["Observability"]
        V[Langfuse Tracing]
    end

    %% Data Flow
    Frontend -->|HTTP/REST| API_Layer
    API_Layer --> Agent_Layer
    
    Agent_Layer --> Tools
    Tools --> Dual_Pipeline
    
    %% Ingestion Flow
    J -->|Query Both| Pipeline_A
    J -->|Query Both| Pipeline_B
    L -->|Ingest| Pipeline_A
    L -->|Ingest| Pipeline_B
    
    %% Retrieval Flow
    Pipeline_A -->|Results| J
    Pipeline_B -->|Results| J
    
    %% LLM Processing
    Agent_Layer --> LLM_Integration
    
    %% External Services
    K -->|Web Search| DuckDuckGo
    
    %% Observability
    Agent_Layer --> Observability
    API_Layer --> Observability

    style Pipeline_A fill:#e1f5fe
    style Pipeline_B fill:#fff3e0
    style Agent_Layer fill:#f3e5f5
    style LLM_Integration fill:#e8f5e8
```
