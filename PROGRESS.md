# Progress Log — Week 1 Completed

A summary of features built, bugs fixed, and architectural choices made during the first week of developing the repository search assistant.

---

## 🚀 What Works

### 1. Ingestion Pipeline & Caching
* **Authentication & Fetching:** [`ingestion/fetcher.py`](ingestion/fetcher.py) uses PyGithub to fetch files directly from the GitHub API using personal access tokens.
* **Offline Cache:** Downloads are saved locally in the `data/raw/` folder as [`readme.json`](data/raw/readme.json) and [`issues.json`](data/raw/issues.json). This allows us to work offline and protects us from API rate limits.
* **Strict Schema Validation:** All records (READMEs, Issues, and PRs) are parsed into a single, standardized Pydantic `Document` shape to guarantee data safety.

### 2. Preprocessing & Noise Reduction
* **Regex Filtering:** The pipeline uses regex engines to strip out hidden HTML comment blocks (`<!-- ... -->`) and excessive spacing from Markdown files.
* **Bot Comment Exclusions:** Comments from known bots (like `dependabot[bot]`, `codspeed-hq[bot]`, and `github-actions[bot]`) are ignored, preserving only human discussions.

### 3. Evaluation Baseline (The Test Key)
* **Hand-Crafted Benchmark:** Created [`eval/questions.json`](eval/questions.json) containing 15 test queries mapped to correct document IDs and gold-standard answers. This will act as our objective grade card when we tune search quality.

---

## 🛠️ What Was Challenging (What's Rough)

* **Windows Console Encoding Bug:** The Windows console defaults to CP1252 encoding. When the fetcher script tried to print issue titles containing Unicode characters (like the arrow emoji `\u2b06`), the script crashed. We resolved this by cleaning console print logs and handling raw string encoding defensively.
* **Python Interactive REPL Pitfall:** Running system commands (like `git status`) inside Python interactive shells (`>>>`) causes syntax crashes. We documented how to exit the REPL shell to keep our shell inputs clean.
* **Pydantic V1/V2 Discrepancies:** Pydantic changed standard model exporters from `.dict()` to `.model_dump()`. We implemented a fallback capability check (`hasattr(doc, "dict")`) to maintain backward compatibility.

---

## 🧠 Key Lessons Learned

1. **Test Early, Parse Local:** Reading parsed local files directly is the fastest way to discover parsing and validation defects.
2. **Prioritize RAG Quality:** Filtering out bot warnings and system notifications early prevents the vector database from storing useless information, saving embedding costs and improving search accuracy.
3. **Commit often:** Keeping clean, labeled git checkpoints ensures development is traceable and easy to review.
