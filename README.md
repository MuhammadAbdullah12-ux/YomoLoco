# YomoLoco (RepoMind) 🧠⚡

**YomoLoco** (also known as **RepoMind**) is an end-to-end Retrieval-Augmented Generation (RAG) and relational metadata sync engine designed to ingest, structure, embed, and query GitHub repositories with high accuracy and minimal noise.

---

## 🚀 Key Features

* **📦 Automated GitHub Ingestion & Filtering:**
  * Ingests READMEs, Issues, and Pull Requests via PyGithub.
  * Filters out bot comments (e.g., `dependabot[bot]`, `github-actions[bot]`, `codspeed-hq[bot]`) to keep index noise minimal.
  * Strips HTML comments (`<!-- ... -->`) and normalizes layout formatting.

* **🔍 Differential Sync Engine (SHA-256 Mutation Detection):**
  * Computes SHA-256 hashes of incoming documents.
  * Dynamically skips unchanged files during sync, updating only modified documents and purging stale vector chunks.

* **⚡ Vector Search & Embeddings:**
  * Employs FastEmbed (`BAAI/bge-small-en-v1.5`, 384 dimensions) for dense text embedding.
  * Stores vector embeddings in a local disk Qdrant instance (`data/qdrant_db`).

* **🗄️ Relational Metadata Store (SQLModel):**
  * Tracks document records (`DocumentRecord`), chunk positions (`ChunkRecord`), and sync audit logs (`SyncLogRecord`) using SQLModel (SQLite / PostgreSQL ready).

* **🌐 FastAPI API Engine:**
  * REST API exposing sync endpoints, metadata retrieval, and system health checks.

* **🎯 Evaluation Benchmark:**
  * Hand-crafted test suites (`eval/questions.json`, `scripts/test_retrieval.py`) for relevance and payload integrity verification.

---

## 🏗️ Project Architecture

```
repomind/
├── backend/
│   ├── app.py          # FastAPI web server & REST API endpoints
│   ├── database.py     # SQLModel engine & session manager
│   ├── models.py       # SQLModel database schemas (Document, Chunk, SyncLog)
│   └── main.py         # Entry point for backend application
├── ingestion/
│   ├── fetcher.py      # PyGithub fetcher & Document Pydantic schema
│   ├── splitter.py     # Markdown-aware & fixed-size chunking utilities
│   ├── embedder.py     # FastEmbed TextEmbedder wrapper (384d)
│   └── pipeline.py     # SyncPipeline master orchestrator engine
├── eval/
│   └── questions.json  # Hand-crafted evaluation dataset (15 test queries)
├── scripts/
│   ├── sync.py            # CLI script to trigger repository sync
│   ├── test_retrieval.py   # Benchmark runner for RAG accuracy (Grade A+)
│   ├── test_chunking.py    # Chunking unit test suite
│   ├── test_embeddings.py  # Embedding similarity test suite
│   ├── test_github.py      # GitHub authentication & fetch verification
│   └── test_postgres.py    # Database connection test suite
├── data/
│   ├── raw/               # Ingested raw JSON datasets
│   └── qdrant_db/         # Local Qdrant vector database storage
├── docker-compose.yml     # Docker services configuration
├── requirements.txt       # Dependencies
└── .env                   # Configuration settings
```

---

## 🛠️ Setup & Installation

### 1. Prerequisites
* Python 3.10+
* Git
* GitHub Personal Access Token (PAT)

### 2. Environment Configuration
Create or update your `.env` file with your GitHub token and target repository:

```env
# Database Configuration
DATABASE_URL=sqlite:///./repomind.db

# Qdrant Vector Store Configuration
QDRANT_URL=local
QDRANT_PATH=./data/qdrant_db

# GitHub Configuration
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPO=MuhammadAbdullah12-ux/YomoLoco
```

### 3. Virtual Environment & Dependencies
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## ⚡ Running the Project

### Execute Ingestion & Sync Pipeline
Run the master sync pipeline script to fetch, chunk, embed, and store document metadata:
```bash
python scripts/sync.py
```

### Start the FastAPI Server
Launch the REST API backend:
```bash
uvicorn backend.app:app --reload --port 8000
```

Access interactive API docs at `http://127.0.0.1:8000/docs`.

### Run Retrieval Benchmark Test
Verify the system health and vector search accuracy:
```bash
python scripts/test_retrieval.py
```

---

## 📊 Evaluation & Verification

The retrieval benchmark suite validates search performance against 15 key queries across multiple technical categories.

| Metric | Target | Status |
| :--- | :--- | :--- |
| **Cosine Similarity Threshold** | `>= 0.55` | ✅ Passed |
| **Payload Integrity** | `100%` | ✅ Passed |
| **System Health Grade** | **A+** | ✅ Operational |

---

## 📜 License

MIT License. Built for repository search and intelligent code workspace analysis.
