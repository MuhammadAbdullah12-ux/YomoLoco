import os
import sys

# Safe print helper for Windows console
def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or 'utf-8'
        print(text.encode(encoding, errors='replace').decode(encoding))

def demonstrate_step2_cross_encoder():
    """
    Step 2 Implementation:
    Loads BAAI/bge-reranker-base using sentence_transformers.CrossEncoder
    and evaluates query-passage pairs to show relevance scoring.
    """
    print("==================================================")
    print("Step 2: Testing BAAI/bge-reranker-base Cross-Encoder")
    print("==================================================")

    print("\n[RUNNING] Loading CrossEncoder model 'BAAI/bge-reranker-base'...")
    try:
        from sentence_transformers import CrossEncoder
        reranker = CrossEncoder("BAAI/bge-reranker-base")
        print("[SUCCESS] CrossEncoder loaded successfully!\n")
    except Exception as e:
        print(f"[ERROR] Failed to load CrossEncoder model: {e}")
        return

    # Sample query and passages for demonstration
    query = "How do I update mcp dependency version to 1.28.1?"
    
    passages = [
        # Passage A: Highly relevant (exact PR details)
        "Title: Bump mcp from 1.26.0 to 1.28.1\nDescription: Bumps mcp version dependency requirement in pyproject.toml.",
        
        # Passage B: Slightly related (mentions mcp, but different topic)
        "Title: Setup model context protocol (mcp) server connection\nDescription: Configures transport protocol layer for mcp.",
        
        # Passage C: Completely irrelevant (OAuth configuration)
        "Title: Fix OAuth2 redirect flows\nDescription: Uses None sentinel instead of mutable default in OAuth2 init."
    ]

    print(f"Query: '{query}'\n")
    print("Evaluating pair relevance scores...\n")

    # Construct (query, passage) pairs
    pairs = [[query, passage] for passage in passages]

    # Predict relevance scores
    scores = reranker.predict(pairs)

    for idx, (passage, score) in enumerate(zip(passages, scores), 1):
        status = "HIGH RELEVANCE" if score > 0 else "LOW / IRRELEVANT"
        print(f"--- Passage {idx} ---")
        print(f"  Relevance Score (Logit): {score:.4f}  [{status}]")
        first_line = passage.split("\n")[0]
        safe_print(f"  Content Preview:         {first_line}")
        print()

    print("==================================================")
    print("Step 2 Verification Complete!")
    print("==================================================")

if __name__ == "__main__":
    demonstrate_step2_cross_encoder()
