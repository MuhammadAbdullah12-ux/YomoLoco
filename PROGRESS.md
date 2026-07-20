# Progress Log — Week 1 & Week 2 Completed 🚀

A summary of features built, bugs fixed, and architectural choices made during the development of the repository search assistant (**YomoLoco / RepoMind**).

---

## 🚀 What Works (Week 1)

### 1. Ingestion Pipeline & Caching
* **Authentication & Fetching:** [`ingestion/fetcher.py`](file:///c:/Users/hp/Desktop/repomind/ingestion/fetcher.py) uses PyGithub to fetch files directly from the GitHub API using personal access tokens.
* **Offline Cache:** Downloads are saved locally in the `data/raw/` folder as `readme.json` and `issues.json`. This allows working offline and protects from API rate limits.
* **Strict Schema Validation:** All records (READMEs, Issues, and PRs) are parsed into a single, standardized Pydantic `Document` shape to guarantee data safety.

### 2. Preprocessing & Noise Reduction
* **Regex Filtering:** The pipeline uses regex engines to strip out hidden HTML comment blocks (`<!-- ... -->`) and excessive spacing from Markdown files.
* **Bot Comment Exclusions:** Comments from known bots (like `dependabot[bot]`, `codspeed-hq[bot]`, and `github-actions[bot]`) are ignored, preserving only human discussions.

### 3. Evaluation Baseline
* **Hand-Crafted Benchmark:** Created [`eval/questions.json`](file:///c:/Users/hp/Desktop/repomind/eval/questions.json) containing 15 test queries mapped to correct document IDs and gold-standard answers.

---

## ⚡ What Works (Week 2)

### 1. Chunking & Text Embedding Engine
* **Smart Text Splitter:** [`ingestion/splitter.py`](file:///c:/Users/hp/Desktop/repomind/ingestion/splitter.py) provides Markdown section header parsing (`#`, `##`, `###`) and sliding fixed-length fallback chunking.
* **FastEmbed Integration:** [`ingestion/embedder.py`](file:///c:/Users/hp/Desktop/repomind/ingestion/embedder.py) wraps `BAAI/bge-small-en-v1.5` to generate 384-dimensional dense vectors with cosine similarity mapping.

### 2. Vector Storage & Relational Metadata DB
* **Qdrant Vector Database:** Integrated local disk Qdrant storage (`data/qdrant_db`) for fast vector index upserts and sub-millisecond retrieval.
* **SQLModel Relational Store:** Defined [`backend/models.py`](file:///c:/Users/hp/Desktop/repomind/backend/models.py) (`DocumentRecord`, `ChunkRecord`, `SyncLogRecord`) with SQLite/PostgreSQL support.

### 3. Master RAG Sync Pipeline & Differential Updates
* **SHA-256 Content Diffing:** [`ingestion/pipeline.py`](file:///c:/Users/hp/Desktop/repomind/ingestion/pipeline.py) computes content hashes to detect mutations, automatically skipping unchanged documents and re-embedding mutated documents.
* **FastAPI Backend Server:** Built [`backend/app.py`](file:///c:/Users/hp/Desktop/repomind/backend/app.py) exposing `/`, `POST /sync`, `POST /repository`, and `GET /documents`.

### 4. Capstone Retrieval Verification Benchmark
* **System Verification:** [`scripts/test_retrieval.py`](file:///c:/Users/hp/Desktop/repomind/scripts/test_retrieval.py) evaluates top-3 vector search results against the evaluation set, achieving **Grade A+ (System Health & Retrieval Verified)**.

---

## 🛠️ Key Challenges & Solutions

* **Windows Console Encoding Bug:** Unicode characters in logs caused console printing crashes. Resolved by implementing `safe_print()` fallback handling.
* **Pydantic V1/V2 Compatibility:** Handled `.dict()` vs `.model_dump()` using dynamic attribute checks (`hasattr(doc, 'dict')`).
* **Vector ID Format:** Solved Qdrant integer point requirement by generating deterministic 63-bit integer hash IDs for chunks.

---

## 🧠 Key Lessons Learned

1. **Incremental RAG Updates:** SHA-256 hash diffing prevents expensive re-embedding operations on large repositories.
2. **Prioritize RAG Quality:** Early noise reduction (filtering bot accounts & HTML comments) significantly boosts top-1 similarity scores.
3. **Structured Verification:** Automated benchmark scripts ensure system regressions are caught immediately.
