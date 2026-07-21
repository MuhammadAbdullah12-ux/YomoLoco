import os
import sys
import json
from datetime import datetime

# Add project root directory to sys.path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from sqlmodel import Session, select
from backend.database import engine
from backend.models import DocumentRecord
from ingestion.pipeline import SyncPipeline

def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or 'utf-8'
        print(text.encode(encoding, errors='replace').decode(encoding))

def run_day5_sync_verification():
    print("==================================================")
    print("Task 4: Day 5 Incremental Sync Verification Test")
    print("==================================================")
    
    target_repo = "fastapi/fastapi"
    
    # 1. Initialize Sync Pipeline
    pipeline = SyncPipeline()
    
    # 2. Run initial sync to ensure we have a baseline and database entries
    print("\n[STEP 1] Running baseline sync (may skip if already sync'd)...")
    try:
        baseline_summary = pipeline.sync_repository(repo=target_repo, force=False)
        print(f"Baseline Summary: Skipped={baseline_summary['docs_skipped']}, Added={baseline_summary['docs_added']}, Updated={baseline_summary['docs_updated']}")
    except Exception as e:
        print(f"[ERROR] Baseline sync failed: {e}")
        pipeline.close()
        sys.exit(1)
        
    # 3. Access SQLite Database and Mutate exactly ONE document
    print("\n[STEP 2] Mutating exactly one document hash in SQLite database...")
    doc_id_mutated = None
    original_hash = None
    
    with Session(engine) as session:
        statement = select(DocumentRecord).where(DocumentRecord.repo == target_repo)
        docs = session.exec(statement).all()
        
        if not docs:
            print("[ERROR] No document records found in the database. Sync baseline is empty.")
            pipeline.close()
            sys.exit(1)
            
        # Select first issue or document to mutate
        target_doc = docs[0]
        doc_id_mutated = target_doc.doc_id
        original_hash = target_doc.content_hash
        
        print(f" -> Selected document: {doc_id_mutated}")
        print(f" -> Original Content Hash: {original_hash}")
        
        # Change content hash to trigger mutation detection on next sync
        target_doc.content_hash = "simulated_mutated_hash_for_test_12345"
        session.add(target_doc)
        session.commit()
        print("[SUCCESS] Mutated content hash stored in SQLite database.")
        
    # 4. Run the sync again to detect the modification
    print("\n[STEP 3] Running sync pipeline again to check mutation detection...")
    try:
        sync_summary = pipeline.sync_repository(repo=target_repo, force=False)
    except Exception as e:
        print(f"[ERROR] Sync pipeline execution failed: {e}")
        # Clean up database mutation state before exiting
        with Session(engine) as session:
            doc = session.get(DocumentRecord, doc_id_mutated)
            if doc:
                doc.content_hash = original_hash
                session.add(doc)
                session.commit()
        pipeline.close()
        sys.exit(1)
        
    # 5. Run Assertions
    print("\n================ Verification Report ================")
    print(f"Total Examined:  {sync_summary['total_documents']}")
    print(f"Added:           {sync_summary['docs_added']}")
    print(f"Updated:         {sync_summary['docs_updated']}")
    print(f"Skipped:         {sync_summary['docs_skipped']}")
    
    # We expect exactly 1 document updated, 0 added, and the rest skipped
    expected_updated = 1
    expected_added = 0
    expected_skipped = sync_summary['total_documents'] - 1
    
    passed = True
    
    if sync_summary['docs_updated'] == expected_updated:
        print(f"  [PASS] Docs Updated count is {sync_summary['docs_updated']} (Expected: {expected_updated})")
    else:
        print(f"  [FAIL] Docs Updated count is {sync_summary['docs_updated']} (Expected: {expected_updated})")
        passed = False
        
    if sync_summary['docs_added'] == expected_added:
        print(f"  [PASS] Docs Added count is {sync_summary['docs_added']} (Expected: {expected_added})")
    else:
        print(f"  [FAIL] Docs Added count is {sync_summary['docs_added']} (Expected: {expected_added})")
        passed = False
        
    if sync_summary['docs_skipped'] == expected_skipped:
        print(f"  [PASS] Docs Skipped count is {sync_summary['docs_skipped']} (Expected: {expected_skipped})")
    else:
        print(f"  [FAIL] Docs Skipped count is {sync_summary['docs_skipped']} (Expected: {expected_skipped})")
        passed = False
        
    pipeline.close()
    
    if passed:
        print("\n[RESULT] Verification status: PASSED (Incremental sync verified successfully)")
        print("==================================================")
        sys.exit(0)
    else:
        print("\n[RESULT] Verification status: FAILED (Assertion mismatches found)")
        print("==================================================")
        sys.exit(1)

if __name__ == "__main__":
    run_day5_sync_verification()
