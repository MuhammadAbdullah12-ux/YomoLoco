import os
import sys

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from fastapi.testclient import TestClient
from backend.app import app, compute_content_hash
from backend.database import init_db

def test_database_and_api():
    print("=========================================")
    print("Testing SQLModel Database & FastAPI Routes...")
    print("=========================================")
    
    # 1. Initialize DB tables
    init_db()
    
    # 2. Test Content Hashing function
    sample_text = "FastAPI framework high-performance web API"
    hash_1 = compute_content_hash(sample_text)
    hash_2 = compute_content_hash(sample_text)
    hash_modified = compute_content_hash(sample_text + " updated")
    
    print(f"\nTesting SHA-256 Content Hashing:")
    print(f"  Original Text Hash:  {hash_1}")
    print(f"  Modified Text Hash:  {hash_modified}")
    assert hash_1 == hash_2, "Error: deterministic hashes must match"
    assert hash_1 != hash_modified, "Error: modified text must produce a different hash"
    print("[SUCCESS] SHA-256 content hashing verified!")

    # 3. Test FastAPI endpoints using TestClient
    print("\nTesting FastAPI API Endpoints...")
    client = TestClient(app)
    
    # Root endpoint test
    response_root = client.get("/")
    print(f"  GET / -> Status Code {response_root.status_code}")
    assert response_root.status_code == 200
    
    # Sync repository metadata endpoint test
    print("\n  Posting to /repository to seed metadata from local JSON cache...")
    response_sync = client.post("/repository?repo=fastapi/fastapi")
    print(f"  POST /repository -> Status Code {response_sync.status_code}")
    print(f"  Response: {response_sync.json()}")
    assert response_sync.status_code == 200
    
    # Get documents endpoint test
    print("\n  Fetching /documents...")
    response_docs = client.get("/documents?repo=fastapi/fastapi")
    print(f"  GET /documents -> Status Code {response_docs.status_code}")
    docs_data = response_docs.json()
    print(f"  Retrieved {docs_data.get('count')} document records from database.")
    assert response_docs.status_code == 200
    assert docs_data.get("count", 0) > 0, "Error: expected at least 1 document record"
    
    # Print sample document record
    sample_doc = docs_data["documents"][0]
    print("\nSample Stored Document Record:")
    print(f"  - ID: {sample_doc.get('doc_id')}")
    print(f"  - Title: {sample_doc.get('title')}")
    print(f"  - Type: {sample_doc.get('doc_type')}")
    print(f"  - Content Hash: {sample_doc.get('content_hash')}")
    print(f"  - URL: {sample_doc.get('url')}")
    
    print("\n[SUCCESS] SQLModel Database & FastAPI Endpoints Verified Successfully!")

if __name__ == "__main__":
    test_database_and_api()
