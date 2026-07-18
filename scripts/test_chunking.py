import os
import json
import sys

# Add project root directory to path to allow importing splitter
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from ingestion.splitter import split_readme, split_text_by_length, count_tokens_approx

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

def test_chunking():
    readme_path = "data/raw/readme.json"
    issues_path = "data/raw/issues.json"
    
    if not os.path.exists(readme_path) or not os.path.exists(issues_path):
        print("[ERROR] Raw JSON data files not found in data/raw/. Please verify you have run ingestion/fetcher.py first.")
        return
        
    print("=========================================")
    print("Testing README Structure-Aware Splitter...")
    print("=========================================")
    with open(readme_path, "r", encoding="utf-8") as f:
        readme_data = json.load(f)
        
    readme_text = readme_data.get("body", "")
    readme_chunks = split_readme(readme_text)
    
    print(f"Total README Chunks generated: {len(readme_chunks)}")
    for i, chunk in enumerate(readme_chunks[:3]):  # Show first 3 chunks as sample
        print(f"\n--- README Chunk {i+1} (approx {count_tokens_approx(chunk)} tokens) ---")
        lines = chunk.strip().split("\n")
        if len(lines) > 8:
            safe_print("\n".join(lines[:4]))
            print("... [TRUNCATED FOR VIEW] ...")
            safe_print("\n".join(lines[-3:]))
        else:
            safe_print(chunk)
            
    # Save README chunks to file for manual inspection
    readme_chunks_path = os.path.join(os.path.dirname(readme_path), "readme_chunks.json")
    with open(readme_chunks_path, "w", encoding="utf-8") as f:
        json.dump(readme_chunks, f, indent=2, ensure_ascii=False)
    print(f"\n[SUCCESS] Saved README chunks to: {readme_chunks_path}")
            
    print("\n=========================================")
    print("Testing Issue/PR Length-Based Splitter with Overlap...")
    print("=========================================")
    with open(issues_path, "r", encoding="utf-8") as f:
        issues_list = json.load(f)
        
    # Search for an issue with significant length to demonstrate splitting
    target_issue = None
    for issue in issues_list:
        body = issue.get("body", "")
        if count_tokens_approx(body) > 600:
            target_issue = issue
            break
            
    if not target_issue and issues_list:
        target_issue = issues_list[0]
        
    if not target_issue:
        print("[ERROR] No issues found in issues.json.")
        return
        
    issue_id = target_issue.get("doc_id", "unknown")
    issue_title = target_issue.get("title", "")
    issue_body = target_issue.get("body", "")
    
    safe_print(f"Selected Issue/PR for testing: {issue_id} - \"{issue_title}\"")
    print(f"Original Text Length: approx {count_tokens_approx(issue_body)} tokens.")
    
    # We will test splitting with a smaller target size (e.g. 200 tokens) to guarantee splitting occurs
    chunks = split_text_by_length(issue_body, max_tokens=200, overlap=30)
    print(f"Generated {len(chunks)} chunks with 30-token overlap limits.")
    
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i+1} (approx {count_tokens_approx(chunk)} tokens) ---")
        lines = chunk.strip().split("\n")
        if len(lines) > 8:
            safe_print("\n".join(lines[:4]))
            print("... [TRUNCATED FOR VIEW] ...")
            safe_print("\n".join(lines[-3:]))
        else:
            safe_print(chunk)

    # Save all issues chunks to file matching our Qdrant schema payload
    all_issue_chunks = []
    for issue in issues_list:
        body = issue.get("body", "")
        # Apply standard max_tokens=500, overlap=50 as per solo plan specification
        issue_chunks = split_text_by_length(body, max_tokens=500, overlap=50)
        for idx, chunk in enumerate(issue_chunks):
            all_issue_chunks.append({
                "doc_id": issue.get("doc_id"),
                "chunk_id": f"{issue.get('doc_id')}-chunk-{idx}",
                "doc_type": issue.get("doc_type"),
                "repo": issue.get("repo"),
                "text": chunk,
                "url": issue.get("url")
            })
            
    issues_chunks_path = os.path.join(os.path.dirname(issues_path), "issues_chunks.json")
    with open(issues_chunks_path, "w", encoding="utf-8") as f:
        json.dump(all_issue_chunks, f, indent=2, ensure_ascii=False)
    print(f"\n[SUCCESS] Saved {len(all_issue_chunks)} issue/PR chunks to: {issues_chunks_path}")

if __name__ == "__main__":
    test_chunking()
