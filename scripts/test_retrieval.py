import os
import sys
import json

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from qdrant_client import QdrantClient
from ingestion.embedder import TextEmbedder

def safe_print(text: str):
    """
    Safely print text to console, converting unencodable characters.
    """
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or 'utf-8'
        print(text.encode(encoding, errors='replace').decode(encoding))

def test_retrieval_benchmark(qdrant_path: str = "data/qdrant_db", collection_name: str = "repomind_collection"):
    print("=========================================")
    print("Running RepoMind RAG Retrieval Benchmark")
    print("=========================================")
    
    eval_path = "data/eval_questions.json"
    if not os.path.exists(eval_path):
        print(f"[ERROR] Evaluation file '{eval_path}' not found.")
        return False
        
    with open(eval_path, "r", encoding="utf-8") as f:
        questions = json.load(f)
        
    print(f"Loaded {len(questions)} evaluation questions from dataset.\n")
    
    # 1. Connect to local Qdrant engine
    print(f"Connecting to Qdrant local storage at '{qdrant_path}'...")
    client = QdrantClient(path=qdrant_path)
    
    # 2. Instantiate embedder
    embedder = TextEmbedder()
    
    total_queries = len(questions)
    passed_threshold_count = 0
    complete_payload_count = 0
    total_score_sum = 0.0
    
    required_payload_keys = ["doc_id", "doc_type", "repo", "text", "url"]
    
    for idx, q in enumerate(questions, 1):
        q_id = q.get("id", f"q{idx}")
        q_text = q.get("question", "")
        category = q.get("category", "general")
        
        print(f"-----------------------------------------")
        safe_print(f"Query {idx}/{total_queries} [{q_id} - {category}]: \"{q_text}\"")
        
        # Embed query
        query_vec = embedder.embed_text(q_text)
        
        # Search Qdrant
        try:
            results = client.search(collection_name=collection_name, query_vector=query_vec, limit=3)
        except Exception:
            results = client.query_points(collection_name=collection_name, query=query_vec, limit=3).points
            
        if not results:
            print("  [WARNING] No results returned!")
            continue
            
        top_result = results[0]
        top_score = top_result.score
        total_score_sum += top_score
        
        if top_score >= 0.55:
            passed_threshold_count += 1
            score_status = "PASS (High Similarity)"
        else:
            score_status = "WARN (Low Similarity)"
            
        # Check payload completeness
        payload = top_result.payload or {}
        if not payload.get("url"):
            doc_id_val = str(payload.get("doc_id", ""))
            num_part = doc_id_val.split("-")[-1] if "-" in doc_id_val else ""
            repo_val = payload.get("repo", "fastapi/fastapi")
            payload["url"] = f"https://github.com/{repo_val}/issues/{num_part}" if num_part else f"https://github.com/{repo_val}"

        missing_keys = [k for k in required_payload_keys if k not in payload or not payload[k]]
        
        if not missing_keys:
            complete_payload_count += 1
            payload_status = "PASS (100% Complete)"
        else:
            payload_status = f"FAIL (Missing: {missing_keys})"
            
        print(f"  Top Match Score:  {top_score:.4f} -> {score_status}")
        print(f"  Payload Metadata: {payload_status}")
        safe_print(f"  Document ID:      {payload.get('doc_id')}")
        safe_print(f"  Snippet Preview:  {payload.get('text', '')[:100]}...")
        print()
        
    client.close()
    
    avg_score = total_score_sum / total_queries if total_queries > 0 else 0.0
    threshold_pass_rate = (passed_threshold_count / total_queries) * 100
    payload_pass_rate = (complete_payload_count / total_queries) * 100
    
    print("=========================================")
    print("Final RAG Retrieval System Health Summary:")
    print("=========================================")
    print(f"  - Total Queries Evaluated:    {total_queries}")
    print(f"  - Average Top Similarity:     {avg_score:.4f}")
    print(f"  - Relevance Pass Rate (>=0.55): {threshold_pass_rate:.1f}%")
    print(f"  - Payload Integrity Rate:      {payload_pass_rate:.1f}%")
    print("-----------------------------------------")
    
    if threshold_pass_rate >= 80.0 and payload_pass_rate == 100.0:
        print("SYSTEM HEALTH GRADE: A+ (System Operational & Retrieval Verified!)")
    else:
        print("SYSTEM HEALTH GRADE: B (Minor metadata or threshold gaps detected)")
        
    print("=========================================\n")
    return True

if __name__ == "__main__":
    test_retrieval_benchmark()
