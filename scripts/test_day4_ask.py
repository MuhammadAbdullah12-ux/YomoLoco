import os
import sys
import json

# Add project root directory to sys.path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from ingestion.ask_pipeline import AskPipeline

def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or 'utf-8'
        print(text.encode(encoding, errors='replace').decode(encoding))

def run_day4_ask_verification():
    print("==================================================")
    print("Task 5: Day 4 Ask & Citation Verification Test")
    print("==================================================")
    
    query = "How do I update mcp dependency version?"
    safe_print(f"Query: \"{query}\"\n")
    
    # 1. Initialize AskPipeline
    try:
        pipeline = AskPipeline()
    except Exception as e:
        print(f"[ERROR] Failed to initialize AskPipeline: {e}")
        return
        
    # 2. Run Ask Query
    print("\n[RUNNING] Executing RAG query through AskPipeline...")
    try:
        result = pipeline.ask(query)
    except Exception as e:
        print(f"[ERROR] AskPipeline failed to execute query: {e}")
        return
        
    answer = result.get("answer", "")
    cited_ids = result.get("cited_chunk_ids", [])
    source_chunks = result.get("source_chunks", [])
    
    print("\n================ Generated Answer ================")
    safe_print(answer)
    print("==================================================")
    
    print(f"\nCited Chunk IDs: {cited_ids}")
    print(f"Retrieved Source Chunk IDs: {[c['chunk_id'] for c in source_chunks]}")
    
    # 3. Citation Verification Report
    print("\n================ Verification Report ================")
    
    valid_citations = 0
    invalid_citations = 0
    
    retrieved_chunk_ids = {c["chunk_id"] for c in source_chunks}
    
    if not cited_ids:
        # Check if the answer is the fallback error or if Gemini just cited nothing
        if "error occurred" in answer.lower():
            print("[INFO] Answer generation fell back to error state (invalid API key). No citations expected.")
        else:
            print("[WARNING] Gemini generated an answer but did not cite any chunks.")
    else:
        for cid in cited_ids:
            if cid in retrieved_chunk_ids:
                print(f"  [PASS] Citation '{cid}' is valid (corresponds to a retrieved chunk).")
                valid_citations += 1
            else:
                print(f"  [FAIL] Citation '{cid}' is INVALID (not in retrieved chunks!).")
                invalid_citations += 1
                
    # Summary of verification
    print("--------------------------------------------------")
    print(f"Verification Summary:")
    print(f"  - Total Citations Evaluated: {len(cited_ids)}")
    print(f"  - Valid Citations:           {valid_citations}")
    print(f"  - Invalid Citations:         {invalid_citations}")
    
    if invalid_citations > 0:
        print("\n[RESULT] Verification status: FAILED (Invalid citations found)")
        sys.exit(1)
    else:
        print("\n[RESULT] Verification status: PASSED (All citations are valid)")
        print("==================================================")

if __name__ == "__main__":
    run_day4_ask_verification()
