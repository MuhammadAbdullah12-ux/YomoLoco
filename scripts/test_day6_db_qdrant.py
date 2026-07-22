import os
import sys
import json
import random

# Add project root directory to sys.path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from sqlmodel import Session, select
from qdrant_client import QdrantClient
from backend.database import engine
from backend.models import DocumentRecord, ChunkRecord

def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or 'utf-8'
        print(text.encode(encoding, errors='replace').decode(encoding))

def run_db_qdrant_audit():
    print("==================================================")
    print("Task 2: SQLite Relational & Qdrant Payload Audit")
    print("==================================================")
    
    qdrant_path = "data/qdrant_db"
    collection_name = "repomind_collection"
    
    if not os.path.exists(qdrant_path):
        print(f"[ERROR] Qdrant storage path '{qdrant_path}' does not exist. Run sync first.")
        sys.exit(1)
        
    # 1. Connect to both DB engines
    print("[RUNNING] Connecting to local Qdrant engine...")
    qdrant_client = QdrantClient(path=qdrant_path)
    
    print("[RUNNING] Querying document records from SQLite...")
    with Session(engine) as session:
        # Retrieve all documents
        statement = select(DocumentRecord)
        docs = session.exec(statement).all()
        
        if not docs:
            print("[ERROR] No documents found in SQLite database. Run sync first.")
            qdrant_client.close()
            sys.exit(1)
            
        print(f" -> Found {len(docs)} document records in SQLite.")
        
        # Select up to 3 random documents to audit
        audit_sample_size = min(3, len(docs))
        audit_docs = random.sample(docs, audit_sample_size)
        print(f" -> Selected {len(audit_docs)} random documents for verification audit.\n")
        
        passed_audits = 0
        failed_audits = 0
        total_chunks_checked = 0
        
        for idx, doc in enumerate(audit_docs, 1):
            print(f"--- Auditing Document #{idx}: '{doc.doc_id}' ({doc.doc_type}) ---")
            
            # Fetch chunks for this document from SQLite
            chunk_statement = select(ChunkRecord).where(ChunkRecord.doc_id == doc.doc_id)
            chunks = session.exec(chunk_statement).all()
            print(f"  - Found {len(chunks)} chunk records in SQLite.")
            
            if not chunks:
                print("  [WARNING] Document has no chunks in SQLite.")
                continue
                
            for chunk in chunks:
                q_id = chunk.qdrant_point_id
                c_id = chunk.chunk_id
                
                # Fetch point from Qdrant
                try:
                    points = qdrant_client.retrieve(
                        collection_name=collection_name,
                        ids=[q_id],
                        with_payload=True,
                        with_vectors=False
                    )
                except Exception as qe:
                    print(f"  [FAIL] Failed to retrieve point {q_id} from Qdrant: {qe}")
                    failed_audits += 1
                    continue
                    
                if not points:
                    print(f"  [FAIL] Point ID {q_id} (Chunk: {c_id}) is missing in Qdrant!")
                    failed_audits += 1
                    continue
                    
                qdrant_point = points[0]
                q_payload = qdrant_point.payload or {}
                
                # Assertions
                text_matches = chunk.text.strip() == q_payload.get("text", "").strip()
                id_matches = doc.doc_id == q_payload.get("doc_id")
                type_matches = doc.doc_type == q_payload.get("doc_type")
                
                total_chunks_checked += 1
                
                if text_matches and id_matches and type_matches:
                    passed_audits += 1
                else:
                    print(f"  [FAIL] Mismatch detected on Chunk ID '{c_id}' (Qdrant Point: {q_id}):")
                    if not text_matches:
                        print("    - Chunk text content does not match!")
                    if not id_matches:
                        print(f"    - Doc ID mismatch: SQLite='{doc.doc_id}', Qdrant='{q_payload.get('doc_id')}'")
                    if not type_matches:
                        print(f"    - Doc Type mismatch: SQLite='{doc.doc_type}', Qdrant='{q_payload.get('doc_type')}'")
                    failed_audits += 1
            
            print(f"  - Document '{doc.doc_id}' audit completed.")
            
    qdrant_client.close()
    
    print("\n================ Verification Report ================")
    print(f"  - Total Chunks Audited:       {total_chunks_checked}")
    print(f"  - Passed Assertions:          {passed_audits}")
    print(f"  - Failed Assertions:          {failed_audits}")
    
    if failed_audits > 0:
        print("\n[RESULT] Verification status: FAILED (Database-Qdrant synchronization mismatches found)")
        print("==================================================")
        sys.exit(1)
    else:
        print("\n[RESULT] Verification status: PASSED (SQLite and Qdrant are in perfect sync)")
        print("==================================================")
        sys.exit(0)

if __name__ == "__main__":
    run_db_qdrant_audit()
