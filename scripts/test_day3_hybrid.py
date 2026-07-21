import os
import sys

# Add project root directory to sys.path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from ingestion.hybrid_retriever import HybridRetriever
from ingestion.reranker import BgeReranker

# Safe print helper to prevent Windows console Unicode crashes
def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or 'utf-8'
        print(text.encode(encoding, errors='replace').decode(encoding))

def run_day3_hybrid_comparison(query: str = "How do I update mcp dependency version?"):
    """
    Task 4 Implementation:
    Pipeline: Hybrid Search (Vector Top-20 + BM25 Top-20 via RRF) -> Cross-Encoder Reranker -> Top-5.
    Prints side-by-side comparison of Pre-Rerank Hybrid Top-5 vs Post-Rerank Top-5.
    """
    print("==================================================================================")
    print("Task 4: Day 3 Hybrid Search + Reranker Integration Pipeline")
    print("==================================================================================")
    safe_print(f"Query: \"{query}\"\n")

    # 1. Initialize Hybrid Retriever & Cross-Encoder Reranker
    hybrid_retriever = HybridRetriever()
    reranker = BgeReranker()

    # 2. Stage 1: Hybrid Search (Vector Top-20 + BM25 Top-20 fused via RRF)
    print("\n[STAGE 1] Performing Hybrid Search (Vector Top-20 + BM25 Top-20 via RRF)...")
    hybrid_top20 = hybrid_retriever.search(query=query, top_k=20, method="rrf")

    # 3. Stage 2: Cross-Encoder Reranking
    print("[STAGE 2] Passing Top-20 Hybrid candidates into BgeReranker (BAAI/bge-reranker-base)...")
    post_rerank_top5 = reranker.rerank(query=query, candidates=hybrid_top20, top_k=5)

    # 4. Display Pre-Rerank Hybrid Top-5 vs Post-Rerank Top-5
    print("\n" + "=" * 82)
    safe_print(" 🔹 STAGE 1: HYBRID SEARCH TOP-5 (Vector + BM25 via RRF)")
    print("=" * 82)
    for rank, item in enumerate(hybrid_top20[:5], 1):
        doc_id = item["doc_id"]
        rrf_score = item["rrf_score"]
        v_rank = item["vector_rank"] if item["vector_rank"] else "-"
        b_rank = item["bm25_rank"] if item["bm25_rank"] else "-"
        snippet = item["text"].replace("\n", " ")[:70]
        safe_print(f"  Rank #{rank} | RRF Score: {rrf_score:.5f} (VecRank: {str(v_rank):<2}, BM25Rank: {str(b_rank):<2}) | Doc: {doc_id:<12} | Snippet: {snippet}...")

    print("\n" + "=" * 82)
    safe_print(" ⚡ STAGE 2: POST-RERANK TOP-5 (BGE Cross-Encoder)")
    print("=" * 82)
    for rank, item in enumerate(post_rerank_top5, 1):
        doc_id = item["doc_id"]
        r_score = item["rerank_score"]
        r_prob = item["rerank_prob"]
        snippet = item["text"].replace("\n", " ")[:70]
        safe_print(f"  Rank #{rank} | Logit: {r_score:+.4f} ({r_prob:.1%}) | Doc: {doc_id:<12} | Snippet: {snippet}...")

    print("\n" + "=" * 82)
    print("Task 4 Day 3 Pipeline Execution Completed Successfully!")
    print("=" * 82 + "\n")

if __name__ == "__main__":
    test_query = "How do I update mcp dependency version?"
    run_day3_hybrid_comparison(query=test_query)
