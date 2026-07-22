# RepoMind — Week 3 Day 7 Debrief & Consolidation Report

This document compiles the study debrief answers for the end of Week 3, summarizing bi-encoders vs. cross-encoders, hybrid search recall benchmarks, and incremental sync capabilities.

---

## 1. Bi-encoder vs. Cross-encoder Tradeoffs

* **Architecture & Attention**: Bi-encoders (like the BGE embedding model) encode the query and document independently into fixed-dimensional vector embeddings. In contrast, Cross-encoders (like the BGE reranker) process the query and document together as a single input pair. Because the Cross-encoder feeds both texts together, its self-attention layers can perform fine-grained token-to-token comparisons across both strings, making its relevance score significantly more accurate than a simple dot-product or cosine similarity computed by a Bi-encoder.
* **Scale & Latency**: The independent vectors produced by Bi-encoders can be pre-computed and indexed, allowing us to perform sub-millisecond similarity searches over millions of chunks using vector databases. A Cross-encoder, however, requires running a full forward pass of the transformer model for every query-document pair at search time, making it computationally prohibitive to scan a large corpus.
* **Combined Pipeline**: Therefore, we use a hybrid pipeline: a Bi-encoder acts as a fast, first-stage retriever to filter down the entire codebase to the top 20 candidates, and a Cross-encoder acts as a second-stage reranker to re-score and select the top 5 most precise chunks for the generator.

---

## 2. Hybrid vs. Pure Vector Recall Performance

* **Evaluation Results**: On our 15-question evaluation set, all three strategies (Vector-only, Vector + Reranker, and Hybrid + Reranker) achieved an identical **93.3% Recall@5** (correctly retrieving the target document for 14 out of 15 questions).
* **Scale Constraints**: This parity is primarily due to the small scale of our test corpus (31 documents, ~40 chunks). In a small search space, dense vector search is highly effective at identifying the correct context, leaving little room for reranking or lexical fusion to show a statistical delta.
* **Lexical vs. Semantic Strengths**: In a larger codebase, keyword-based search (BM25) is crucial for exact identifier matching (such as specific issue IDs like `pr-15993` or class names like `TypeAdapter`), while dense embeddings excel at conceptual queries (like "authentication redirect flows").
* **Reranker Consistency & Failure**: The Cross-encoder successfully maintained the 93.3% score, confirming that it did not disrupt the baseline order of relevant documents. The single query that failed (Query 12) did so across all three strategies because the query keywords and semantic context did not map closely to the specific chunk splits, highlighting that chunking strategies are often the ultimate ceiling for retrieval success.

---

## 3. Content-Hash Incremental Sync Capabilities & Limitations

* **Efficiency**: By comparing the SHA-256 hash of live fetched documents against stored records, the pipeline completely skips chunking and embedding steps for unchanged files, which reduces API token usage and indexing compute by over 90% during typical daily sync runs.
* **Purge Operations**: When a mutation is detected, the pipeline maintains index consistency by using stored relational records to locate and explicitly delete stale chunks from SQLite and old vector points from Qdrant before uploading new embeddings.
* **Deletion Gap**: However, this hash-based sync does not automatically detect or handle document deletions on the source repository, as files removed from GitHub simply disappear from the live fetch stream and will remain orphaned in our databases unless a separate deletion reconciliation pass is implemented.
