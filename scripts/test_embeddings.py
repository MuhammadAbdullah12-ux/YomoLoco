import os
import sys
import json

# Add root folder to sys.path to allow importing ingestion modules
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from ingestion.embedder import TextEmbedder
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

def safe_print(text: str):
    """
    Safely print text to console, converting unencodable characters to fallback characters.
    Prevents crash on Windows consoles when printing emojis like \u2b06.
    """
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or 'utf-8'
        print(text.encode(encoding, errors='replace').decode(encoding))

def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    Computes cosine similarity between two normalized vectors.
    Since TextEmbedder normalizes output vectors to unit length (1.0),
    the cosine similarity is equal to the simple dot product.
    """
    return sum(a * b for a, b in zip(vec1, vec2))

def test_similarity():
    print("=========================================")
    print("Testing TextEmbedder and Cosine Similarity...")
    print("=========================================")
    
    # 1. Instantiate the embedder
    embedder = TextEmbedder()
    
    # 2. Define test strings
    similar_text_1 = "fix deadlocks in database depends by using a separate CapacityLimiter threadpool"
    similar_text_2 = "concurrency thread pool deadlock occurring during database connection teardowns"
    
    unrelated_text_1 = "fix deadlocks in database depends by using a separate CapacityLimiter threadpool"
    unrelated_text_2 = "correct typo spelling errors and fix broken 404 links in documentation pages"
    
    print("\nEncoding sentences...")
    vec_sim_1 = embedder.embed_text(similar_text_1)
    vec_sim_2 = embedder.embed_text(similar_text_2)
    vec_unrel_2 = embedder.embed_text(unrelated_text_2)
    
    # Verify dimensions (BAAI/bge-small-en-v1.5 must output 384 dimensions)
    print(f"Embedding vector dimensions: {len(vec_sim_1)} (Expected: 384)")
    assert len(vec_sim_1) == 384, f"Error: expected 384 dimensions, got {len(vec_sim_1)}"
    
    # 3. Calculate similarities
    sim_score = cosine_similarity(vec_sim_1, vec_sim_2)
    unrel_score = cosine_similarity(vec_sim_1, vec_unrel_2)
    
    print(f"\nComparing similar concepts:")
    print(f"  A: \"{similar_text_1}\"")
    print(f"  B: \"{similar_text_2}\"")
    print(f"  -> Cosine Similarity: {sim_score:.4f}")
    
    print(f"\nComparing unrelated concepts:")
    print(f"  A: \"{unrelated_text_1}\"")
    print(f"  B: \"{unrelated_text_2}\"")
    print(f"  -> Cosine Similarity: {unrel_score:.4f}")
    
    # Assertions to verify correctness (calibrated to BGE embedding distribution range)
    print("\nRunning assertions...")
    assert sim_score > 0.7, f"Error: similar sentences should have high similarity, got {sim_score:.4f}"
    assert unrel_score < 0.6, f"Error: unrelated sentences should have low similarity, got {unrel_score:.4f}"
    print("[SUCCESS] Cosine similarity sanity checks passed successfully!")

def test_qdrant_load():
    print("\n=========================================")
    print("Testing Qdrant Local Engine and Collection Setup...")
    print("=========================================")
    
    # 1. Establish connection to local disk-based Qdrant engine (Zero Docker required!)
    storage_path = "data/qdrant_db"
    print(f"Initializing Qdrant Local Disk Engine at: '{storage_path}'...")
    client = QdrantClient(path=storage_path)
    print("[SUCCESS] Local Qdrant engine initialized successfully!")

    collection_name = "repomind_collection"
    
    # 2. Check and initialize collection with Cosine Distance and 384 dimensions
    print(f"Setting up collection '{collection_name}' with 384 dimensions...")
    try:
        if client.collection_exists(collection_name):
            client.delete_collection(collection_name)
    except Exception:
        pass
        
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
    print(f"[SUCCESS] Collection '{collection_name}' is initialized.")
    
    # 3. Load sample chunks from local files and embed them
    chunks_path = "data/raw/issues_chunks.json"
    if not os.path.exists(chunks_path):
        print(f"[ERROR] Chunks file '{chunks_path}' not found. Please run scripts/test_chunking.py first.")
        return False
        
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks_data = json.load(f)
        
    # We will pick the first 5 chunks to upload as a test
    test_chunks = chunks_data[:5]
    print(f"Loaded {len(test_chunks)} test chunks from file.")
    
    embedder = TextEmbedder()
    
    points = []
    for idx, item in enumerate(test_chunks):
        text = item.get("text", "")
        print(f"  Embedding chunk {idx}...")
        vector = embedder.embed_text(text)
        
        points.append(PointStruct(
            id=idx,
            vector=vector,
            payload={
                "doc_id": item.get("doc_id"),
                "chunk_id": item.get("chunk_id"),
                "doc_type": item.get("doc_type"),
                "repo": item.get("repo"),
                "text": text,
                "url": item.get("url")
            }
        ))
        
    # 4. Upsert into Qdrant
    print(f"Upserting {len(points)} points into Qdrant collection...")
    client.upsert(
        collection_name=collection_name,
        wait=True,
        points=points
    )
    print("[SUCCESS] Upsert completed successfully!")
    
    # 5. Run a quick search query to verify Qdrant is functioning
    query_text = "how do I resolve deadlocks in database connections"
    query_vector = embedder.embed_text(query_text)
    
    print(f"\nRunning test query search for: \"{query_text}\"...")
    try:
        search_results = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=2
        )
    except Exception:
        # Compatibility fallback for newer qdrant-client versions
        search_results = client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=2
        ).points
    
    print("\nSearch Results:")
    for result in search_results:
        print(f"  - Point ID: {result.id}, Score: {result.score:.4f}")
        safe_print(f"    Text: {result.payload.get('text')[:100]}...")
        
    print("\n[SUCCESS] Qdrant local verification completed successfully!")
    return True

if __name__ == "__main__":
    test_similarity()
    test_qdrant_load()
