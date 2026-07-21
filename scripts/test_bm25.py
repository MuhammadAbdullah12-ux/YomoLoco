import os
import sys

# Add project root directory to sys.path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from ingestion.bm25_retriever import BM25Retriever

# Safe print helper to prevent Windows console Unicode crashes
def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or 'utf-8'
        print(text.encode(encoding, errors='replace').decode(encoding))

def run_test_bm25():
    """
    Test script to verify BM25 Lexical Keyword Search.
    Tests keyword queries like PR numbers, exact method names, and general concepts.
    """
    print("==================================================================================")
    print("Task 2 Test: BM25 Lexical Keyword Search Verification")
    print("==================================================================================")

    print("[RUNNING] Initializing BM25Retriever and indexing corpus...")
    retriever = BM25Retriever()
    print(f"[SUCCESS] Indexed {len(retriever.corpus_chunks)} chunks into BM25 index.\n")

    test_queries = [
        "PR 15993 mutable default argument in OAuth2",
        "APIRouter route caching static paths PR 15963",
        "How do I update mcp dependency version?"
    ]

    for q_idx, query in enumerate(test_queries, 1):
        print("-" * 82)
        safe_print(f"Query #{q_idx}: \"{query}\"")
        print("-" * 82)

        results = retriever.search(query=query, top_k=5)

        if not results:
            print("  ⚠️ No matching documents found for query.\n")
            continue

        for rank, item in enumerate(results, 1):
            doc_id = item["doc_id"]
            doc_type = item["doc_type"]
            bm25_score = item["bm25_score"]
            snippet = item["text"].replace("\n", " ")[:90]

            safe_print(f"  Rank #{rank:02d} | BM25 Score: {bm25_score:6.2f} | Type: {doc_type:<5} | Doc ID: {doc_id}")
            safe_print(f"           Snippet: {snippet}...\n")

    print("==================================================================================")
    print("Task 2 BM25 Test Completed Successfully!")
    print("==================================================================================")

if __name__ == "__main__":
    run_test_bm25()
