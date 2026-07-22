import math
import torch
torch.set_num_threads(1)
from typing import List, Dict, Any
from sentence_transformers import CrossEncoder


_RERANKER_CACHE = {}

class BgeReranker:
    """
    Stage 2 Precision Reranker Wrapper.
    Uses BAAI/bge-reranker-base Cross-Encoder to re-score and re-order
    candidate document chunks retrieved from Stage 1 Vector Search.
    """
    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self.model_name = model_name
        if model_name not in _RERANKER_CACHE:
            print(f"[RUNNING] Loading Reranker model: '{model_name}'...")
            _RERANKER_CACHE[model_name] = CrossEncoder(model_name)
            print(f"[SUCCESS] Reranker model '{model_name}' ready!")
        self.model = _RERANKER_CACHE[model_name]


    @staticmethod
    def _logit_to_sigmoid(logit: float) -> float:
        """
        Converts raw cross-encoder logit into a normalized [0, 1] probability score.
        """
        return 1.0 / (1.0 + math.exp(-float(logit)))

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Reranks a list of candidate chunk dictionaries for a given query string.
        
        Each candidate dictionary should contain at least:
          - "text" or "content": The text snippet of the chunk.
          - "doc_id": Unique identifier for the source document.
          
        Returns:
          Top-K reranked list of candidate dictionaries updated with:
          - "rerank_score": Raw logit score from CrossEncoder.
          - "rerank_prob": Normalized Sigmoid probability [0.0 - 1.0].
        """
        if not candidates:
            return []

        # 1. Extract candidate text strings
        pairs = []
        for cand in candidates:
            chunk_text = cand.get("text") or cand.get("content") or ""
            pairs.append([query, chunk_text])

        # 2. Compute cross-encoder relevance logits
        raw_scores = self.model.predict(pairs)

        # 3. Attach rerank metrics to candidates
        reranked_results = []
        for cand, score in zip(candidates, raw_scores):
            score_float = float(score)
            cand_copy = dict(cand)
            cand_copy["rerank_score"] = score_float
            cand_copy["rerank_prob"] = self._logit_to_sigmoid(score_float)
            reranked_results.append(cand_copy)

        # 4. Sort candidates descending by raw logit score
        reranked_results.sort(key=lambda x: x["rerank_score"], reverse=True)

        # 5. Return top-K candidates
        return reranked_results[:top_k]
