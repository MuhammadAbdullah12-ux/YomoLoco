# RepoMind — Week 4 Day 1 Evaluation Baseline

This document logs the baseline retrieval performance scores of the RepoMind RAG engine across 15 hand-written queries.

---

## 📊 Summary Metrics

* **Evaluation Dataset**: `15 hand-labeled benchmark questions`
* **Target Metric**: `Recall@5` (the percentage of queries where the target document is found in the top-5 retrieved chunks)
* **Overall System Grade**: **A+**

| Strategy Configuration | Recall@5 Score | Target Hits |
| :--- | :---: | :---: |
| **Strategy 1: Vector-Only Search** | **93.3%** | 14 / 15 |
| **Strategy 2: Vector + Reranker** | **93.3%** | 14 / 15 |
| **Strategy 3: Hybrid + Reranker** | **93.3%** | 14 / 15 |

---

## 🔍 Detailed Query-by-Query Breakdown

| # | Category | Query Text | Vector Only | Vec+Rerank | Hybrid+Rerank | Target ID |
| :-: | :--- | :--- | :---: | :---: | :---: | :--- |
| **01** | `factual_lookup` | What are the two core library dependencies that FastAPI stands on? | **PASS** | **PASS** | **PASS** | `readme-fastapi/fastapi` |
| **02** | `factual_lookup` | How do you start a local development server for a FastAPI application? | **PASS** | **PASS** | **PASS** | `readme-fastapi/fastapi` |
| **03** | `code_reference` | What issue does PR 15993 address in OAuth2.\_\_init\_\_? | **PASS** | **PASS** | **PASS** | `pr-15993` |
| **04** | `code_reference` | What optimization was introduced to APIRouter in pull request 15963? | **PASS** | **PASS** | **PASS** | `pr-15963` |
| **05** | `code_reference` | Why does using 'from \_\_future\_\_ import annotations' cause ForwardRef warnings when using Annotated types... | **PASS** | **PASS** | **PASS** | `pr-15411` |
| **06** | `code_reference` | What causes thread deadlocks when running teardown in dependencies, and how does PR 15388 resolve it? | **PASS** | **PASS** | **PASS** | `pr-15388` |
| **07** | `code_reference` | What performance bottleneck in 'jsonable_encoder' does pull request 15965 optimize? | **PASS** | **PASS** | **PASS** | `pr-15965` |
| **08** | `factual_lookup` | What is the purpose of Swagger UI in a FastAPI application, and what is its standard URL path? | **PASS** | **PASS** | **PASS** | `readme-fastapi/fastapi` |
| **09** | `factual_lookup` | How do you declare optional query parameters in FastAPI route functions? | **PASS** | **PASS** | **PASS** | `readme-fastapi/fastapi` |
| **10** | `factual_lookup` | How does the performance of FastAPI compare to NodeJS and Go? | **PASS** | **PASS** | **PASS** | `readme-fastapi/fastapi` |
| **11** | `factual_lookup` | What alternative API documentation interface does FastAPI provide besides Swagger UI? | **PASS** | **PASS** | **PASS** | `readme-fastapi/fastapi` |
| **12** | `factual_lookup` | What changes did YuriiMotov make in PR 15967? | **FAIL** | **FAIL** | **FAIL** | `pr-15967` |
| **13** | `code_reference` | How does PR 15965 handle SQLAlchemy models safely while skipping recursive encoding? | **PASS** | **PASS** | **PASS** | `pr-15965` |
| **14** | `factual_lookup` | What capacity limit value was chosen for the teardown thread limiter in PR 15388 and why? | **PASS** | **PASS** | **PASS** | `pr-15388` |
| **15** | `factual_lookup` | How does FastAPI perform data validation and conversion under the hood? | **PASS** | **PASS** | **PASS** | `readme-fastapi/fastapi` |

---

## 💡 Key Analysis & Observations

1. **High Parity**: Due to the compact nature of the test codebase corpus (31 documents), dense vector retrieval alone was highly successful, enabling all configurations to score 14/15 hits. Reranking and hybrid keyword matches did not disrupt this ranking baseline.
2. **Query 12 Failure Mode**: Query 12 failed because the query "What changes did YuriiMotov make in PR 15967?" requires matching exact author name keys and PR IDs inside a document body that primarily details redirect and URL link cleanups. Future work in Week 5 (e.g. metadata extraction) could enrich chunks with author and pull request metadata tags to enable 100% search coverage.
