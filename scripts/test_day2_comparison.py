import os
import sys

# Add project root directory to sys.path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from qdrant_client import QdrantClient
from ingestion.embedder import TextEmbedder
from ingestion.reranker import BgeReranker

# Safe print helper to prevent Windows console Unicode crashes
def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or 'utf-8'
        print(text.encode(encoding, errors='replace').decode(encoding))

def run_day2_comparison(query: str = "How do I update mcp dependency version?"):
    """
    Task 3 Implementation:
    Retrieves top-20 candidates from Stage 1 Vector Search (Qdrant),
    runs Stage 2 Cross-Encoder Reranker, and prints side-by-side comparison
    of Pre-Rerank Top-5 vs. Post-Rerank Top-5.
    """
    qdrant_path = "data/qdrant_db"
    collection_name = "repomind_collection"

    print("==================================================================================")
    print("Task 3: Side-by-Side Comparison (Stage 1 Vector vs. Stage 2 Reranker)")
    print("==================================================================================")
    safe_print(f"Query: \"{query}\"\n")

    # 1. Connect to Qdrant & Embed Query
    client = QdrantClient(path=qdrant_path)
    embedder = TextEmbedder()
    query_vec = embedder.embed_text(query)

    # 2. Stage 1: Vector Search (Fetch Top-20 candidates)
    print("[STAGE 1] Fetching top-20 candidate chunks from Qdrant vector store...")
    try:
        results = client.search(collection_name=collection_name, query_vector=query_vec, limit=20)
    except Exception:
        results = client.query_points(collection_name=collection_name, query=query_vec, limit=20).points

    candidates = []
    for point in results:
        payload = point.payload or {}
        candidates.append({
            "doc_id": payload.get("doc_id", "N/A"),
            "doc_type": payload.get("doc_type", "N/A"),
            "vector_score": point.score,
            "text": payload.get("text", "")
        })

    client.close()

    # 3. Stage 2: Rerank Top-20 using Cross-Encoder
    print("[STAGE 2] Passing top-20 candidates into BgeReranker (BAAI/bge-reranker-base)...")
    reranker = BgeReranker()
    reranked_top5 = reranker.rerank(query=query, candidates=candidates, top_k=5)

    # 4. Display Pre-Rerank Top-5 vs. Post-Rerank Top-5
    print("\n" + "="*82)
    safe_print(" 🔹 PRE-RERANK (Stage 1 Vector Search Top-5) ")
    print("="*82)
    for rank, item in enumerate(candidates[:5], 1):
        doc_id = item["doc_id"]
        v_score = item["vector_score"]
        snippet = item["text"].replace("\n", " ")[:70]
        safe_print(f"  Rank #{rank} | Sim Score: {v_score:.4f} | Doc: {doc_id:<12} | Snippet: {snippet}...")

    print("\n" + "="*82)
    safe_print(" ⚡ POST-RERANK (Stage 2 Cross-Encoder Top-5) ")
    print("="*82)
    for rank, item in enumerate(reranked_top5, 1):
        doc_id = item["doc_id"]
        r_score = item["rerank_score"]
        r_prob = item["rerank_prob"]
        snippet = item["text"].replace("\n", " ")[:70]
        safe_print(f"  Rank #{rank} | Logit: {r_score:+.4f} ({r_prob:.1%}) | Doc: {doc_id:<12} | Snippet: {snippet}...")

    print("\n" + "="*82)
    print("Task 3 Visual Comparison Completed Successfully!")
    print("="*82 + "\n")

if __name__ == "__main__":
    test_query = "How do I update mcp dependency version?"
    run_day2_comparison(query=test_query)
