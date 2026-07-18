import os
import sys
import json

# Add root folder to sys.path to allow importing ingestion modules
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from ingestion.embedder import TextEmbedder

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
    
    # 1. Instantiate the embedder (downloads weights if first time)
    embedder = TextEmbedder()
    
    # 2. Define test strings
    # We will test two groups of sentences to confirm similarity math:
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

if __name__ == "__main__":
    test_similarity()
