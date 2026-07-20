import os
import sys
from qdrant_client import QdrantClient

# Add project root directory to sys.path so imports work cleanly
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from ingestion.embedder import TextEmbedder

# Safe print helper to prevent Windows console Unicode crashes
def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or 'utf-8'
        print(text.encode(encoding, errors='replace').decode(encoding))

def run_step3_retrieval(query: str = "How do I update mcp dependency version?", top_k: int = 20):
    """
    Step 3 Implementation:
    Queries Qdrant vector store and retrieves top-K (20) raw vector matches
    based on cosine similarity of 384d dense embeddings.
    """
    qdrant_path = "data/qdrant_db"
    collection_name = "repomind_collection"

    print("==================================================")
    print(f"Step 3: Stage 1 Vector Retrieval (Top-{top_k})")
    print("==================================================")
    
    if not os.path.exists(qdrant_path):
        print(f"[ERROR] Qdrant database directory '{qdrant_path}' not found. Run sync first.")
        return

    # 1. Connect to Qdrant Local Engine
    print(f"[RUNNING] Connecting to Qdrant local database at: '{qdrant_path}'...")
    client = QdrantClient(path=qdrant_path)

    # 2. Instantiate TextEmbedder (BAAI/bge-small-en-v1.5)
    print("[RUNNING] Initializing TextEmbedder (BAAI/bge-small-en-v1.5)...")
    embedder = TextEmbedder()

    # 3. Convert text query into 384-dimensional vector embedding
    safe_print(f"\n[QUERY]: \"{query}\"")
    print("[RUNNING] Converting query text into 384-dimensional vector...")
    query_vec = embedder.embed_text(query)

    # 4. Search Qdrant vector database for top-K nearest neighbors
    print(f"[RUNNING] Searching Qdrant collection '{collection_name}' for top-{top_k} nearest matches...")
    try:
        results = client.search(collection_name=collection_name, query_vector=query_vec, limit=top_k)
    except Exception:
        results = client.query_points(collection_name=collection_name, query=query_vec, limit=top_k).points

    print(f"\n================ Top-{len(results)} Vector Search Candidates ================\n")

    for rank, point in enumerate(results, 1):
        score = point.score
        payload = point.payload or {}
        doc_id = payload.get("doc_id", "N/A")
        doc_type = payload.get("doc_type", "N/A")
        text = payload.get("text", "").replace("\n", " ")
        snippet = text[:100] + ("..." if len(text) > 100 else "")

        # Format visual score status
        if score >= 0.75:
            quality = "🔥 EXCELLENT"
        elif score >= 0.60:
            quality = "✅ GOOD"
        else:
            quality = "⚠️ WEAK / NOISE"

        safe_print(f"Rank {rank:02d} | Similarity: {score:.4f} [{quality}] | Type: {doc_type:<5} | Doc ID: {doc_id}")
        safe_print(f"        Snippet: {snippet}\n")

    client.close()
    print("==================================================")
    print("Step 3 Retrieval Execution Finished Successfully!")
    print("==================================================")

if __name__ == "__main__":
    test_query = "How do I update mcp dependency version?"
    run_step3_retrieval(query=test_query, top_k=20)
