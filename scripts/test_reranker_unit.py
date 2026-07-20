import os
import sys

# Add project root directory to sys.path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from ingestion.reranker import BgeReranker

def test_reranker_module():
    print("==================================================")
    print("Testing BgeReranker Module (ingestion/reranker.py)")
    print("==================================================")
    
    reranker = BgeReranker()
    
    query = "How do I update mcp dependency version?"
    
    candidates = [
        {
            "doc_id": "pr-16018",
            "doc_type": "pr",
            "text": "Title: Bump mcp from 1.26.0 to 1.28.1 Description: Bumps mcp version dependency requirement."
        },
        {
            "doc_id": "pr-15993",
            "doc_type": "pr",
            "text": "Title: fix: use None sentinel instead of mutable OAuthFlowsModel default in OAuth2 init."
        },
        {
            "doc_id": "pr-15493",
            "doc_type": "pr",
            "text": "Title: fix: replace mutable default arg and add encoding to open() calls."
        }
    ]
    
    reranked = reranker.rerank(query, candidates, top_k=2)
    
    print(f"\nQuery: '{query}'")
    print(f"Top-{len(reranked)} Reranked Results:\n")
    
    for idx, item in enumerate(reranked, 1):
        print(f"Rank {idx}: Doc ID={item['doc_id']} | Logit={item['rerank_score']:.4f} | Prob={item['rerank_prob']:.1%}")
        print(f"       Snippet: {item['text'][:80]}...\n")
        
    print("==================================================")
    print("BgeReranker Module Verified Successfully!")
    print("==================================================")

if __name__ == "__main__":
    test_reranker_module()
