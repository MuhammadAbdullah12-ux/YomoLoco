import os
import torch
torch.set_num_threads(1)
from sentence_transformers import SentenceTransformer


_MODEL_CACHE = {}

class TextEmbedder:
    """
    Utility wrapper to load BAAI/bge-small-en-v1.5 and generate
    384-dimensional vector embeddings for chunked text.
    """
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        if model_name not in _MODEL_CACHE:
            print(f"[RUNNING] Loading embedding model: {model_name}...")
            # SentenceTransformer will download and cache the model weights locally
            _MODEL_CACHE[model_name] = SentenceTransformer(model_name)
            print(f"[SUCCESS] Model loaded successfully.")
        self.model = _MODEL_CACHE[model_name]
        self.dimension = self.model.get_sentence_embedding_dimension()


    def embed_text(self, text: str) -> list[float]:
        """
        Encodes a single text string into a 384-dimensional list of floats.
        Automatically normalizes vector length to 1.0.
        """
        if not text or not text.strip():
            return [0.0] * self.dimension
        embedding = self.model.encode(text, convert_to_numpy=False, normalize_embeddings=True)
        return list(embedding)

    def embed_chunks(self, chunks: list[str]) -> list[list[float]]:
        """
        Encodes a batch list of string chunks.
        Automatically normalizes vector lengths to 1.0.
        """
        if not chunks:
            return []
        # Filter out empty strings to avoid errors
        cleaned_chunks = [c if c.strip() else " " for c in chunks]
        embeddings = self.model.encode(cleaned_chunks, convert_to_numpy=False, normalize_embeddings=True)
        return [list(emb) for emb in embeddings]
