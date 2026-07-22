import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import sys
import json

# Add project root directory to sys.path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from fastapi.testclient import TestClient
from backend.app import app

def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or 'utf-8'
        print(text.encode(encoding, errors='replace').decode(encoding))

def run_integration_test():
    print("==================================================")
    print("Task 1: End-to-End API Integration & Verification")
    print("==================================================")
    
    # 1. Initialize TestClient
    client = TestClient(app)
    
    # 2. Test Root Endpoint
    print("\n[STEP 1] Querying GET / (Root Health Check)...")
    res_root = client.get("/")
    assert res_root.status_code == 200
    safe_print(f"Response: {res_root.json()}")
    
    # 3. Test Sync Endpoint
    target_repo = "fastapi/fastapi"
    print(f"\n[STEP 2] Querying POST /sync?repo={target_repo}...")
    res_sync = client.post(f"/sync?repo={target_repo}")
    assert res_sync.status_code == 200
    sync_data = res_sync.json()
    print(f"Sync Result: Status={sync_data['status']}, Skipped={sync_data['docs_skipped']}, Added={sync_data['docs_added']}, Updated={sync_data['docs_updated']}")
    
    # 4. Test 10 Questions on POST /ask
    test_queries = [
        "How do I update mcp dependency version?",
        "What are standard optional dependencies in FastAPI?",
        "What does replace mutable default arg fix do?",
        "Does FastAPI support Pydantic and Starlette?",
        "How to use TypeAdapter.validate_json?",
        "Where are OAuth2 redirect flows modified?",
        "How do I configure custom request timeout?",
        "Is there an offline cache implemented?",
        "Who is the author of python-sdk bump pr?",
        "Does it filter automated system bot accounts?"
    ]
    
    print(f"\n[STEP 3] Sending {len(test_queries)} queries to POST /ask...")
    
    passed_queries = 0
    failed_queries = 0
    
    for idx, query in enumerate(test_queries, 1):
        print(f"\n--- Query #{idx:02d}: \"{query}\" ---")
        payload = {"query": query}
        res_ask = client.post("/ask", json=payload)
        
        if res_ask.status_code != 200:
            print(f"  [FAIL] HTTP status code: {res_ask.status_code}")
            failed_queries += 1
            continue
            
        data = res_ask.json()
        
        # Check dictionary schema keys
        has_answer = "answer" in data
        has_citations = "cited_chunk_ids" in data
        has_sources = "source_chunks" in data
        
        if has_answer and has_citations and has_sources:
            print("  [PASS] Response JSON matches expected RAG schema.")
            print(f"  Snippet: {data['answer'][:80]}...")
            print(f"  Source count: {len(data['source_chunks'])}")
            passed_queries += 1
        else:
            print("  [FAIL] Response JSON has missing schema keys.")
            failed_queries += 1
            
    print("\n================ Verification Summary ================")
    print(f"  - Total API Queries Run:  {len(test_queries)}")
    print(f"  - Successful API Queries: {passed_queries}")
    print(f"  - Failed API Queries:     {failed_queries}")
    
    if failed_queries > 0:
        print("\n[RESULT] Verification status: FAILED (API schema validation failures)")
        print("==================================================")
        sys.exit(1)
    else:
        print("\n[RESULT] Verification status: PASSED (All endpoints integrated successfully)")
        print("==================================================")
        sys.exit(0)

if __name__ == "__main__":
    run_integration_test()
