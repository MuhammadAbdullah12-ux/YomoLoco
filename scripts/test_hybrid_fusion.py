import os
import sys

# Add project root directory to sys.path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from ingestion.hybrid_retriever import HybridRetriever

# Safe print helper to prevent Windows console Unicode crashes
def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or 'utf-8'
        print(text.encode(encoding, errors='replace').decode(encoding))

def run_test_hybrid_fusion():
    """
    Test script for Task 3: Hybrid Fusion (Vector + BM25 using RRF and Min-Max scaling).
    """
    print("==================================================================================")
    print("Task 3 Test: Hybrid Retrieval Fusion Verification (RRF vs Min-Max)")
    print("==================================================================================")

    print("[RUNNING] Initializing HybridRetriever (loading Qdrant vector engine + BM25 index)...")
    hybrid = HybridRetriever()

    test_queries = [
        "PR 15993 mutable default argument in OAuth2",
        "How do I update mcp dependency version?"
    ]

    for q_idx, query in enumerate(test_queries, 1):
        print("\n" + "=" * 82)
        safe_print(f"Query #{q_idx}: \"{query}\"")
        print("=" * 82)

        # 1. Run RRF Fusion
        print("\n[FUSION METHOD 1] Reciprocal Rank Fusion (RRF)")
        print("-" * 82)
        rrf_results = hybrid.search(query=query, top_k=5, method="rrf")

        for rank, item in enumerate(rrf_results, 1):
            doc_id = item["doc_id"]
            rrf_score = item["rrf_score"]
            v_rank = item["vector_rank"] if item["vector_rank"] else "-"
            b_rank = item["bm25_rank"] if item["bm25_rank"] else "-"
            snippet = item["text"].replace("\n", " ")[:70]

            safe_print(f"  Rank #{rank:02d} | RRF Score: {rrf_score:.5f} | Vec Rank: {str(v_rank):<2} | BM25 Rank: {str(b_rank):<2} | Doc ID: {doc_id}")
            safe_print(f"           Snippet: {snippet}...")

        # 2. Run Min-Max Fusion
        print("\n[FUSION METHOD 2] Min-Max Normalization Weighted Sum (alpha=0.5)")
        print("-" * 82)
        minmax_results = hybrid.search(query=query, top_k=5, method="minmax", alpha=0.5)

        for rank, item in enumerate(minmax_results, 1):
            doc_id = item["doc_id"]
            h_score = item["hybrid_score"]
            v_norm = item["vector_norm"]
            b_norm = item["bm25_norm"]
            snippet = item["text"].replace("\n", " ")[:70]

            safe_print(f"  Rank #{rank:02d} | Hybrid Score: {h_score:.4f} (VecNorm: {v_norm:.2f}, BM25Norm: {b_norm:.2f}) | Doc ID: {doc_id}")
            safe_print(f"           Snippet: {snippet}...")

    print("\n" + "=" * 82)
    print("Task 3 Hybrid Fusion Test Completed Successfully!")
    print("=" * 82 + "\n")

if __name__ == "__main__":
    run_test_hybrid_fusion()
