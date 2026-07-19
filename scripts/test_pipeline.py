import os
import sys

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from ingestion.pipeline import SyncPipeline
from fastapi.testclient import TestClient
from backend.app import app

def test_pipeline_execution():
    print("=========================================")
    print("Testing End-to-End Master RAG Pipeline...")
    print("=========================================")
    
    # 1. Run Pipeline Run #1 (Fresh Sync)
    print("\n--- Pipeline Run #1 (Fresh Data Sync) ---")
    pipeline = SyncPipeline()
    summary_1 = pipeline.sync_repository(repo="fastapi/fastapi")
    
    print(f"Run #1 Summary:")
    print(f"  Docs Added:        {summary_1['docs_added']}")
    print(f"  Docs Updated:      {summary_1['docs_updated']}")
    print(f"  Docs Skipped:      {summary_1['docs_skipped']}")
    print(f"  Chunks Vectorized: {summary_1['chunks_created']}")
    
    assert summary_1["docs_added"] > 0 or summary_1["docs_updated"] > 0 or summary_1["docs_skipped"] > 0, "Error: expected documents to be processed"
    print("[SUCCESS] First sync run executed cleanly!")

    # 2. Run Pipeline Run #2 (Idempotency & Hash Diffing Check)
    print("\n--- Pipeline Run #2 (Idempotency & Hash Diffing Check) ---")
    summary_2 = pipeline.sync_repository(repo="fastapi/fastapi")
    
    print(f"Run #2 Summary:")
    print(f"  Docs Added:        {summary_2['docs_added']}")
    print(f"  Docs Updated:      {summary_2['docs_updated']}")
    print(f"  Docs Skipped:      {summary_2['docs_skipped']}")
    print(f"  Chunks Vectorized: {summary_2['chunks_created']}")
    
    assert summary_2["docs_skipped"] == summary_2["total_documents"], "Error: expected all documents to be skipped on unchanged run"
    assert summary_2["chunks_created"] == 0, "Error: no new chunks should be created on unchanged run"
    pipeline.close()
    print("[SUCCESS] Second sync run idempotency check passed! (All unchanged documents skipped).")

    # 3. Test FastAPI POST /sync endpoint via TestClient
    print("\n--- Testing FastAPI POST /sync Endpoint ---")
    client = TestClient(app)
    response = client.post("/sync?repo=fastapi/fastapi")
    print(f"  POST /sync -> Status Code {response.status_code}")
    print(f"  Response Payload: {response.json()}")
    assert response.status_code == 200
    assert response.json()["docs_skipped"] > 0
    print("[SUCCESS] FastAPI POST /sync endpoint verified!")

    print("\n[SUCCESS] End-to-End Master Pipeline Verification Completed Successfully!")

if __name__ == "__main__":
    test_pipeline_execution()
