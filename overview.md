# Service Manual Chat Application Specification

## 1. Objective

Design a chat application using OSS (open-source software) that can ingest service manuals through two channels:
- **(a)** Direct document upload
- **(b)** Automatic web retrieval (no manual URL input)

The application should answer user questions with high factual accuracy. API calls to foundational models are permissible (OpenAI, Anthropic, Gemini, etc) and encouraged.

### Key Features:
- Store embeddings in two different vector databases
- Each database fed by distinct chunking + embedding pipeline
- Agent should choose best strategy for ingesting/retrieving context
- Primary use case: Troubleshooting/diagnostics chat for:
  - Commercial refrigeration
  - Late-model automobiles

## 2. Functional Requirements

| ID | Capability               | Details |
|----|--------------------------|---------|
| F1 | Document Upload + Ingestion | UI lets a user upload PDF/DOCX |
| F2 | Auto Web Retrieval | Agent infers correct manual from chat context:<br>- Asks for missing make/model/manufacturer info<br>- Runs web search (SerpAPI/Google Search API)<br>- Locates most likely PDF/HTML manual<br>- Downloads and extracts information<br>- Ingests via active pipeline |
| F3 | Dual Pipelines | **Pipeline A**:<br>- RecursiveTextSplitter → text-embedding-3-large → pgvector<br><br>**Pipeline B**:<br>- Semantic Section Splitter → all-MiniLM-L12-v2 → Pinecone<br><br>Make chunk size/overlap obvious in code |
| F4 | Chat Interface | Single-page web UI (React/Streamlit/Gradio) + websocket/REST API<br>- Free-text questions<br>- Answers include citations (doc name + page/URL) |

## 3. Technical Requirements

Developer's discretion - choose the stack, but minimize use of "AI-as-a-Service" tools.

## 4. Deliverables

GitHub repository containing:

- `README.md` covering:
  - Quick-start (Docker Compose)
  - Architecture diagram
  - Description of both pipelines and rationale