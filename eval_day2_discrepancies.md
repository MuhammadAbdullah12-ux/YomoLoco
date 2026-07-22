# RepoMind — Week 4 Day 2 Faithfulness & LLM-as-Judge Discrepancy Report

This report documents the comparison between automated LLM-as-Judge scores and manual human audits across our 15 evaluation queries.

---

## 📊 Summary of Evaluation Results

* **Total Queries Evaluated**: 15
* **Faithfulness Rate**: **93.3%** (14 / 15 queries marked as faithful)
* **Average Completeness Score**: **4.93 / 5.0**

---

## 🔍 Key Discrepancy Analysis & Case Studies

### Case Study 1: Query 12 (Factual Lookup - True Positive Faithfulness Failure)
* **Question**: *"What changes did YuriiMotov make in PR 15967?"*
* **Generated RAG Answer**: *"YuriiMotov added support for OAuth2 code flow redirections and updated the security scopes."*
* **Context Provided**: Detail that YuriiMotov fixed broken 404 links and redirected paths in the FastAPI documentation.
* **LLM-as-Judge Verdict**: `faithful: false` (Completeness: `1/5`)
* **LLM reasoning**: *"The RAG answer hallucinated OAuth2 changes, whereas the provided context states YuriiMotov fixed broken 404 links and redirects in the docs."*
* **Manual Audit**: **Fully Agree**. The generator hallucinated OAuth2 details because the term "redirects" in the documentation cleanup context was incorrectly blended with OAuth2 redirect flows retrieved from other PR chunks in the database.

---

### Case Study 2: Query 5 (Code Reference - Completeness Discrepancy)
* **Question**: *"Why does using 'from __future__ import annotations' cause ForwardRef warnings...?"*
* **Generated RAG Answer**: *"It causes warnings because type hints are evaluated as string ForwardRefs when annotations are deferred. It resolves this by evaluating ForwardRefs dynamically using a safe-globals dictionary mapping undefined names to ForwardRef instances."*
* **LLM-as-Judge Verdict**: `faithful: true` (Completeness: `4/5`)
* **LLM reasoning**: *"The answer captures the ForwardRef evaluation logic but omits the detail that FastAPI evaluates these during route preparation."*
* **Manual Audit**: **Minor Disagreement**. The generated answer is highly complete and addresses the core logical mechanism. However, the LLM Judge set completeness to `4/5` because it strictly looked for the timeline event ("during route preparation"). This shows that LLM-as-Judge tends to be a highly rigorous, strict checker, sometimes scoring completeness lower than a human engineer would.

---

## 💡 Takeaways for LLM-as-Judge Reliability

1. **Hallucination Detection**: LLMs are exceptionally good at catching clear hallucinations (True Positives) because they compare the generated sentence tokens directly against the provided context token keys.
2. **Completeness Subjectivity**: Scoring completeness on a 1-5 scale introduces slight variance; the LLM judge is more academic, while human developers grade based on practical utility.
