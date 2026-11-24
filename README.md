# MindBridge AI: Secure Multimodal Conversational Assistant

MindBridge AI is an enterprise-grade multimodal conversational assistant engineered with high-entropy anonymous session isolation, Retrieval-Augmented Generation (RAG) over PDFs and text documents, pluggable multimodal adapters (Text, Vision, STT, and TTS), and layered safety guardrails.

---

## 1. Architecture Overview

```
Streamlit Frontend (Port 8501)
         |
         | HTTP REST (X-Session-ID header)
         v
FastAPI Application (Port 8000)
    ├── Chat Service
    ├── Multimodal Input Router (Image Vision, Audio STT, Audio TTS)
    ├── RAG Pipeline (PyMuPDF Ingestion, Chunking, Embeddings, Vector Retrieval)
    ├── Safety & Guardrail Engine (Crisis Lifelines, Diagnostic Refusal, Injection Defense)
    ├── Conversation Service & Session Isolation
    └── SQLAlchemy 2.x Repositories
             |
             v
       MySQL 8.0 (Primary Relational Database)
```

### Key Engineering Decisions:
- **Decoupled Architecture**: The Streamlit UI communicates strictly via HTTP with the FastAPI application, eliminating direct database exposure.
- **Anonymous Session Isolation**: Users are protected without forced authentication. High-entropy 64-character tokens (`X-Session-ID`) enforce strict data segregation across conversations, messages, and uploaded documents.
- **MySQL & Relational Vector Storage**: Document chunk embeddings are persisted relationally in MySQL `document_chunks` records. Vector similarity search executes via vectorized cosine similarity (`numpy`) over the active session's indexed chunks. This eliminates external vector DB overhead while preserving full MySQL 8.0 compatibility and zero-code migration path to MySQL 9+ Vector or dedicated vector stores.
- **Prompt Injection Defense**: Retrieved document text is treated as untrusted reference data and isolated within `<retrieved_context>` XML boundaries. The system explicitly instructs the LLM not to execute commands contained within documents.
- **Non-Clinical Empathetic Support**: Warm, patient, non-judgmental assistance with strict refusal of medical/psychiatric diagnoses or medication prescriptions, paired with an emergency crisis intervention protocol.

---

## 2. Prerequisites & Environment Setup

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- MySQL Server 8.0+ (optional for local testing; SQLite fallback is supported)

### Installation Steps

1. **Clone or Navigate to the Workspace**:
   ```bash
   cd c:\Users\hp\Downloads\chatbot
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy the `.env.example` template to `.env`:
   ```bash
   copy .env.example .env
   ```

---

## 3. Configuration & Environment Variables

| Variable | Description | Default |
|---|---|---|
| `ENVIRONMENT` | Runtime environment (`development` / `production`) | `development` |
| `DATABASE_URL` | MySQL connection string | `mysql+pymysql://root:password@localhost:3306/mindbridge` |
| `ALLOW_SQLITE_DEV_FALLBACK` | Allow SQLite dev database if MySQL is unreachable | `true` |
| `LLM_PROVIDER` | LLM provider (`mock`, `gemini`, `openai`) | `mock` |
| `LLM_API_KEY` | API key for Gemini / OpenAI | Empty |
| `EMBEDDING_PROVIDER` | Embedding provider (`mock`, `gemini`, `openai`) | `mock` |
| `VISION_PROVIDER` | Vision provider (`mock`, `gemini`, `openai`) | `mock` |
| `STT_PROVIDER` | Speech-to-Text provider (`mock`, `openai`) | `mock` |
| `TTS_PROVIDER` | Text-to-Speech provider (`mock`, `openai`) | `mock` |
| `RAG_CHUNK_SIZE` | Character length per chunk | `500` |
| `RAG_CHUNK_OVERLAP` | Overlap character count between chunks | `50` |
| `RAG_TOP_K` | Number of chunks retrieved per query | `4` |
| `RAG_RELEVANCE_THRESHOLD`| Minimum cosine similarity score | `0.35` |
| `MAX_DOCUMENT_SIZE_MB` | Maximum allowed document upload size | `10` |
| `MAX_PDF_PAGES` | Maximum page count for PDF documents | `50` |

---

## 4. Database Setup & Migrations

### Running MySQL
To start MySQL Server on Windows:
```cmd
net start MySQL80
```
Or use MySQL Workbench / command line:
```sql
CREATE DATABASE IF NOT EXISTS mindbridge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Applying Alembic Migrations
Run database migrations using Alembic:
```bash
alembic upgrade head
```

---

## 5. Running the Application

### Option A: Using the Dev Launcher Script
```bash
# 1. Run configuration diagnostic
python scripts/run_dev.py check

# 2. Start FastAPI Backend (Port 8000)
python scripts/run_dev.py backend

# 3. In a separate terminal, start Streamlit Frontend (Port 8501)
python scripts/run_dev.py frontend
```

### Option B: Starting Services Directly

1. **FastAPI Backend**:
   ```bash
   uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   Interactive API docs are available at: `http://127.0.0.1:8000/docs`

2. **Streamlit Frontend**:
   ```bash
   streamlit run frontend/streamlit_app.py --server.port 8501
   ```
   Web interface opens at: `http://localhost:8501`

---

## 6. API Endpoint Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status and provider configuration |
| `GET` | `/api/session/new` | Issues fresh 64-character anonymous session token |
| `POST` | `/api/conversations` | Creates conversation for active session |
| `GET` | `/api/conversations` | Lists conversations for active session |
| `GET` | `/api/conversations/{id}` | Retrieves conversation details and messages |
| `DELETE` | `/api/conversations/{id}` | Deletes conversation and cascades to messages |
| `POST` | `/api/chat` | Text chat with RAG retrieval and optional TTS |
| `POST` | `/api/chat/multimodal` | Multipart chat with image understanding |
| `POST` | `/api/documents` | Ingests, chunks, embeds, and indexes PDF/TXT document |
| `GET` | `/api/documents` | Lists indexed documents for active session |
| `DELETE` | `/api/documents/{id}` | Deletes document and cleans up chunks |
| `POST` | `/api/audio/transcribe` | Transcribes audio file (WAV, MP3, WebM) |
| `POST` | `/api/audio/synthesize` | Synthesizes text into audio stream |
| `POST` | `/api/feedback` | Records helpful/unhelpful rating on message |

All API endpoints (except `/health` and `/api/session/new`) require the header:
```
X-Session-ID: <64-character-hex-token>
```

---

## 7. Running Automated Tests

Run the complete test suite without requiring paid API calls or live external network access:
```bash
python -m pytest backend/tests -v
```

Test coverage includes:
- **API & Database**: Healthcheck, session header validation, conversation CRUD, session isolation, cascade deletion.
- **RAG Subsystem**: Text chunking, PDF page extraction, vector cosine similarity ranking, citation verification, document cleanup, empty retrieval honest handling.
- **Multimodal**: Valid/invalid image signatures, vision analysis, audio transcription, audio synthesis.
- **Safety & Guardrails**: Crisis/self-harm intervention, psychiatric diagnosis refusal, drug dosage refusal, prompt injection defense, indirect document injection containment.

---

## 8. MVP Limitations & Production Readiness Roadmap

### Current MVP Scope
- Single-user anonymous session isolation via cryptographic headers (no user login or RBAC).
- Local or self-hosted vector similarity search over session-scoped documents.
- Upload limits: 10MB document size, 50-page PDF limit, 5MB image limit, 10MB audio limit.

### Recommended Steps Before Public Production Deployment
1. **User Authentication & RBAC**: Integrate OAuth2 / OpenID Connect (e.g. Auth0, Keycloak) for persistent cross-device user accounts.
2. **Distributed Cache & Rate Limiting**: Introduce Redis for distributed token-bucket rate limiting and session caching.
3. **Advanced Vector Search**: As document volume scales beyond tens of thousands of chunks, attach MySQL HeatWave Vector Search, pgvector, or a dedicated vector database (Qdrant, Milvus).
4. **End-to-End Encryption**: Encrypt document chunks and conversation payloads at rest using envelope encryption (e.g., AWS KMS or HashiCorp Vault).
5. **Auditing & Telemetry**: Integrate OpenTelemetry for distributed tracing and structured security audit logging.
