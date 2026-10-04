# Echoes of an Era

> **Tagline:** *"A living AI time capsule built from my grandfather's voice."*

---

## Project Overview

**Echoes of an Era** is an open-source, retrieval-grounded AI voice memory capsule designed to preserve, organize, search, and revisit a grandfather's authentic life stories and wisdom.

Our grandfathers lived through monumental transformations in everyday life, communication, education, workplace dynamics, travel, and family traditions. While many of these stories exist only in unscripted conversations or personal audio recordings, traditional audio archives are difficult to search, index, and explore.

The goal of this project is to create an interactive interface to those recorded memories without turning the AI into a fictionalized, hallucinatory avatar of him.

> **Core Principle:**  
> *"AI interprets the memories. It does not create the memories."*  
> The original voice recordings remain the immutable single source of truth.

---

## The Problem

- **Fragile Oral Histories:** Personal family stories and historical insights are easily lost over time.
- **Unsearchable Audio Archives:** Hours of raw voice recordings are difficult to browse or query for specific life topics.
- **Disappearing Perspectives:** Future generations miss out on firsthand historical context because they don’t know which questions to ask.
- **AI Hallucination Risk:** Generic conversational AI models tend to fabricate details when asked personal family questions, creating fictional narratives rather than preserving authentic history.

*Built specifically for my grandfather during the Hacktoberfest 2026 DEV Weekend Challenge ("Build for a Friend").*

---

## Screenshots

![alt text](images/image.png)
![alt text](images/image-8.png)
![alt text](images/image-7.png)
![alt text](images/image-1.png)
![alt text](images/image-2.png)
![alt text](images/image-3.png)
![alt text](images/image-4.png)
![alt text](images/image-5.png)
![alt text](images/image-6.png)
---

## The Solution

**Echoes of an Era** processes authentic voice recordings through a pipeline of local Speech-to-Text transcription, structured memory extraction, high-dimensional vector embeddings, hybrid search, and retrieval-grounded Q&A.

### High-Level System Flow

```mermaid
flowchart LR
    A[Grandfather's Voice Recording] --> B[faster-whisper STT]
    B --> C[Gemma 3 Memory Extraction]
    C --> D[BGE-M3 Dense Vector Embeddings]
    D --> E[(PostgreSQL + pgvector)]
    E --> F[Hybrid Retrieval Engine]
    F --> G[Grounded RAG Pipeline]
    G --> H[Grounded Answer]
    G --> I[Verbatim Quotes & Source Badges]
    I --> J[Streaming Original Audio Playback]
```

Users ask natural-language questions about his life and receive evidence-based answers strictly tied to authentic recordings, with verbatim quotes and timestamped audio playback.

---

## Key Features

- 🎙️ **Audio Memory Vaulting:** Upload and store raw voice recordings (`.mp3`, `.wav`, `.m4a`) up to 100MB per file with automatic PyAV audio metadata decoding.
- 📝 **Timestamped Speech-to-Text:** Verbatim transcription using `faster-whisper` (`large-v3-turbo`) with voice activity detection (VAD) and auto-detected language support (Hindi, Hinglish, English).
- 🧠 **Structured Memory Extraction:** Automatically extracts titles, summaries, historical eras, locations, people mentioned, emotions, verbatim quotes, and life advice using `gemma3:1B-Q4_K_M` running locally through Docker Model Runner.
- ⚡ **1024-Dimensional Vector Search:** High-density semantic indexing using local `BAAI/bge-m3` via `SentenceTransformers` stored in PostgreSQL with `pgvector` HNSW vector indexes.
- 🔍 **Hybrid Retrieval Engine:** Combines dense vector similarity with keyword/lexical field scoring re-ranked via Reciprocal Rank Fusion (RRF).
- 💬 **Grounded Q&A ("Ask Grandfather"):** Answers user questions strictly using retrieved memory context, refusing to fabricate answers when evidence is insufficient.
- 🎧 **Interactive Audio Player & Timestamps:** Direct, range-supported HTTP audio streaming that jump-cuts to the exact second where grandfather spoke the retrieved memory.
- 📜 **Chronological Era Timeline:** Explore memories grouped chronologically across eras (1940s to present) and filter by thematic categories.
- ⏳ **"Then vs Now" Reflections:** Compare historical experiences described by grandfather (THEN) against modern realities (NOW), generating generational reflection questions and enduring values.

---

## Why This Is Different

This application is **NOT** an "AI chatbot pretending to be my grandfather."  
It **IS** an **AI interface to my grandfather's authentic memories.**

| Generic Personal AI / Chatbot | Echoes of an Era |
| :--- | :--- |
| Roleplays as the deceased/elderly person | Acts as a transparent archival librarian |
| Hallucinates stories when information is missing | Refuses politely when evidence is absent from recordings |
| Generates unverified synthetic responses | Provides verbatim quotes & direct audio playback links |
| Disconnects answer from original source | Anchors every claim to exact audio timestamps |

---

## Architecture

### System Architecture Diagram

```mermaid
graph TD
    subgraph Client Layer
        UI[React 18 + Vite Frontend]
        Player[Docked Audio Player]
    end

    subgraph Backend Services FastAPI
        API[FastAPI Application]
        STT[faster-whisper STT Service]
        Embed[BAAI/bge-m3 Embedding Service]
        Retriever[Hybrid Retrieval Service]
        RAG[Grounded RAG Service]
        Comp[Then vs Now Comparison Service]
    end

    subgraph Local AI Engine
        DMR[Docker Model Runner]
        Gemma[Gemma 3 1B Q4_K_M Model]
    end

    subgraph Database Layer
        PG[(PostgreSQL 16 + pgvector)]
        Storage[Local Audio Storage ./uploads/audio]
    end

    UI -->|REST API| API
    API --> STT
    API --> Embed
    API --> Retriever
    API --> RAG
    API --> Comp
    
    STT --> Storage
    Embed -->|1024-dim Dense Vectors| PG
    Retriever -->|HNSW Vector + Keyword Search| PG
    RAG -->|Prompt Context| DMR
    Comp -->|Prompt Context| DMR
    DMR --> Gemma
    Player -->|Range Stream| API
    API -->|Audio Bytes| Storage
```

---

## AI Architecture

### 1. Speech-to-Text (STT)
- **Model:** `faster-whisper` (`large-v3-turbo` model default).
- **Execution:** Local Python runtime with CTranslate2 and PyAV.
- **Features:** Voice Activity Detection (`vad_filter=True`), beam size 5, initial prompt context priming for elder speech (Hindi / Hinglish / English), non-destructive segment timestamping (`start_time`, `end_time`).

### 2. Large Language Model (LLM)
- **Model:** `gemma3:1B-Q4_K_M` (Gemma 3 1B quantized).
- **Runtime:** `Gemma 3 1B Q4_K_M running locally through Docker Model Runner` (`http://localhost:12434`).
- **Tasks:**
  - Structured memory schema extraction (`temperature: 0.1`, JSON mode).
  - Evidence-grounded response generation (`temperature: 0.2`).
  - Historical comparison synthesis ("Then vs Now").

### 3. Embeddings & Vector Representation
- **Model:** `BAAI/bge-m3` via `SentenceTransformers`.
- **Dimensions:** Exactly 1024-dimensional normalized dense vectors.
- **Execution:** Strictly local execution (`EMBEDDING_LOCAL_ONLY=true`) loaded from Hugging Face cache. No model truncation, padding, or fallback to lower-dimensional models.
- **Composite Input Schema:** Encodes `TITLE + SUMMARY + TOPICS + TRANSCRIPT`.

### 4. Database & Vector Indexing
- **Engine:** PostgreSQL 16 with `pgvector` extension.
- **Index:** HNSW cosine similarity vector index (`Vector(1024)`).

### 5. Hybrid Retrieval & Score Fusion
- **Vector Search:** Cosine similarity calculation (`1.0 - cosine_distance`).
- **Keyword Search:** Multi-field lexical frequency scoring across memory title, tags, summary, verbatim quotes, life advice, and full transcript text.
- **Score Fusion:** Reciprocal Rank Fusion (RRF $k=60$) combined with weighted linear scoring (65% vector weight + 35% keyword weight + dual match bonus).

### 6. Grounding and Hallucination Control
- **Retrieval Threshold:** Minimum score threshold ($\ge 0.15$) and strict candidate score floor ($\ge 0.20$).
- **Insufficient Evidence Guardrail:** If no retrieved memories meet the confidence floor, the system refuses to guess and outputs:
  > *"Grandfather has not spoken about this in his recorded memories."*
- **Source Verification:** Every valid response returns source metadata containing memory ID, title, verbatim quote, and precise audio playback timestamps.

---

## Example User Journey

1. **User Query:** *"How did Grandpa send letters to his parents when he moved for high school?"*
2. **Hybrid Search:** The retrieval engine queries PostgreSQL `pgvector` for 1024-dim embedding proximity while scanning keyword tokens (`letters`, `communicated`, `school`).
3. **Candidate Matching:** Retrieves `Memory ID: cd682ea1-b4af-4c18-b04c-8e57d32ee2da` titled *"Early Childhood and Writing Letters Home"*.
4. **Context Assembly:** Assembles memory context including time period (1950s), verbatim quotes, and audio timestamp bounds ($12.4\text{s} \to 84.2\text{s}$).
5. **Gemma 3 Generation:** Local Gemma 3 model processes prompt with strict grounding constraints.
6. **Response Output:** Generates a concise summary explaining that grandfather wrote weekly inland letters, posted them at the village post office, and waited 7–10 days for a response.
7. **Source Badge Display:** Renders a interactive citation card with verbatim quote: *"Hum har Ravivar ko chitthi likhte the..."*
8. **Audio Trigger:** User clicks the citation playback button.
9. **Audio Stream:** The backend streams `audio.mp3` from timestamp $12.4\text{s}$.
10. **Verification:** The user hears their grandfather’s actual voice telling the story.

---

## Validation

The project was validated against real-world test scenarios:
- **Audio Processing:** Processed 3–5 authentic grandfather voice recordings.
- **Pipeline Execution:** Verified end-to-end flow: Audio file upload $\to$ Whisper STT $\to$ Gemma 3 memory extraction $\to$ BGE-M3 1024-dim embedding $\to$ pgvector storage $\to$ Hybrid RAG search.
- **Q&A Evaluation:** Tested with 5+ factual questions (correctly retrieved and answered) and 3+ out-of-archive/unanswerable questions (e.g., questions about modern topics like Bitcoin or 2024 tech).
- **Refusal Behavior:** Confirmed that unanswerable queries triggered the exact guardrail refusal without hallucinating facts.
- **User Feedback:** Grandfather tested the interface to review his recorded memories.

---

## Built for a Real Person

This project was conceived and built specifically for my grandfather. Rather than serving as an abstract technical concept, every design decision—from high-contrast UI fonts and simple navigation to exact audio playback links—was tailored to respect and preserve his living legacy.

---

## Open Source / Open Innovation

Open-weight AI and open-source infrastructure are fundamental for personal family archives:
- **Local / Open-Weight LLM:** Using `gemma3:1B-Q4_K_M` ensures family memories can be queried without sending private family transcripts to external third-party LLM providers.
- **Local Embedding Model:** `BAAI/bge-m3` runs completely on-device without cloud API dependencies.
- **Data Sovereignty:** Family history remains stored in standard open formats (PostgreSQL, WAV/MP3, JSON).
- **Long-Term Accessibility:** Open architecture guarantees the time capsule remains accessible even if commercial cloud services change pricing or shut down.

---

## Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React 18, Vite, Tailwind CSS, Lucide React | Modern responsive Web UI & docked audio player |
| **Backend** | FastAPI, Python 3.10+, PyAV, Pydantic | Async REST API & streaming media server |
| **Database** | PostgreSQL 16 | Relational storage for memories, transcripts, & eras |
| **Vector Search** | `pgvector` (0.2.5+) | 1024-dim HNSW vector similarity search |
| **LLM Model** | Gemma 3 1B Q4_K_M (`gemma3:1B-Q4_K_M`) | Memory extraction, grounded Q&A, Then vs Now |
| **LLM Runtime** | Docker Model Runner (`docker model`) | Local LLM inference engine (port 12434) |
| **Embeddings** | `BAAI/bge-m3` (SentenceTransformers) | 1024-dimensional normalized dense vectors |
| **Speech-to-Text** | `faster-whisper` (`large-v3-turbo`) | Local audio transcription & timestamp extraction |
| **Containerization**| Docker & Docker Compose | Containerized database and vector engine setup |

---

## Project Structure

```text
Echoes-of-an-Era/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI Routers (memories, ask, compare, search)
│   │   ├── db/              # Database session & pgvector initialization
│   │   ├── models/          # SQLAlchemy ORM models (AudioRecord, ExtractedMemory, etc.)
│   │   ├── prompts/         # Grounding prompt templates (extraction, rag, comparison)
│   │   ├── schemas/         # Pydantic response/request schemas
│   │   └── services/        # Services (STT, Embeddings, LLM, Retrieval, RAG, Comparison)
│   ├── clean_db.py          # Database cleanup & maintenance utility
│   ├── download_bge_m3.py   # Pre-downloads BGE-M3 weights into HF cache
│   ├── Dockerfile           # Backend container image definition
│   ├── requirements.txt     # Python dependencies
│   └── test_*.py            # Automated test suites (RAG, STT, Embeddings, Hybrid Search)
├── frontend/
│   ├── src/
│   │   ├── components/      # React components (AudioPlayer, AudioUploader, MemoryCard, etc.)
│   │   ├── pages/           # Pages (Home, Timeline, Ask, Compare)
│   │   ├── services/        # Client API SDK (`api.js`)
│   │   ├── App.jsx          # Router & main application shell
│   │   └── index.css        # Design tokens & glassmorphism CSS
│   ├── package.json         # Node.js dependencies
│   └── vite.config.js       # Vite dev server configuration
├── data/                    # Local Docker volume mounts (PostgreSQL data)
├── docker-compose.yml       # Docker service definition for PostgreSQL + pgvector
├── .env.example             # Safe environment variable configuration template
└── .gitignore               # Excludes secrets, node_modules, and raw audio files
```

---

## Local Development Setup

### Prerequisites
- **Python:** 3.10+
- **Node.js:** 18+
- **Docker Desktop:** Installed and running (with Docker Model Runner support)

### 1. Clone & Configure Environment
```bash
git clone https://github.com/NegiSushant/Echoes-of-an-Era.git
cd Echoes-of-an-Era
cp .env.example .env
```

### 2. Start PostgreSQL with pgvector
```bash
docker-compose up -d postgres
```

### 3. Run Gemma 3 via Docker Model Runner
Ensure Gemma 3 1B Q4_K_M is pulled and running locally on port 12434:
```bash
docker model run gemma3:1B-Q4_K_M
```

### 4. Setup & Start Backend
```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt

# Pre-download local embedding model weights (required once)
python download_bge_m3.py

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

### 5. Setup & Start Frontend
In a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Environment Variables

Refer to `.env.example` for full configuration details:

```env
# Database (PostgreSQL + pgvector)
POSTGRES_USER=echoes
POSTGRES_PASSWORD=echoes_password
POSTGRES_DB=echoes_of_an_era
DATABASE_URL=postgresql://echoes:echoes_password@localhost:5432/echoes_of_an_era

# LLM Service (Docker Model Runner)
LLM_BASE_URL=http://localhost:12434
LLM_MODEL=gemma3:1B-Q4_K_M

# STT & Embedding Models
WHISPER_MODEL_SIZE=large-v3-turbo
EMBEDDING_MODEL_NAME=BAAI/bge-m3
DEVICE=cpu
EMBEDDING_LOCAL_ONLY=true
```

---

## API Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status & core principles |
| `POST` | `/api/memories/upload` | Ingest raw audio file (`.mp3`, `.wav`, `.m4a`) |
| `POST` | `/api/memories/{id}/pipeline` | Run STT transcription $\to$ Gemma extraction $\to$ BGE-M3 embedding |
| `GET` | `/api/memories` | List extracted memories with era/category filtering |
| `GET` | `/api/memories/timeline` | Get aggregated chronological era timeline metadata |
| `GET` | `/api/memories/audio/{id}/stream` | Stream raw audio with HTTP Range support |
| `POST` | `/api/search` | Execute hybrid vector + keyword memory search |
| `POST` | `/api/ask` | Ask a question via grounded RAG (returns answer + audio sources) |
| `POST` | `/api/compare` | Generate "Then vs Now" reflection with source audio |

---

## Limitations

- **Hardware Constraints:** Local LLM inference speed depends on host CPU/GPU capabilities.
- **Audio Quality Dependence:** Noisy or heavily degraded vintage tape recordings may require manual review of Speech-to-Text outputs.
- **Single-Family Dataset Scale:** Designed primarily for deep indexing of an individual elder's memory archive rather than multi-tenant enterprise search.

---

## Future Improvements

- **Multilingual Audio Diarization:** Separate multiple speakers automatically in joint family interviews.
- **Emotion & Tone Tagging:** Extract subtle acoustic emotional queues directly from voice pitch and pace.
- **Printable Memory Books:** Generate formatted PDF family memory albums with QR codes linking to original voice recordings.

---

## Hackathon

- **Challenge:** Hacktoberfest 2026 DEV Weekend Challenge — *"Build for a Friend"*
- **Target Recipient:** Built for my grandfather.
- **Core Focus:** Real-world problem solving powered by open-weight AI models.

---

## License

This project is open-source. (See repository root for licensing terms).
