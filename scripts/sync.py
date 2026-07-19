import os
import sys
import argparse

# Add root folder to sys.path to allow importing ingestion modules
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from ingestion.pipeline import SyncPipeline

def main():
    parser = argparse.ArgumentParser(
        description="Master RAG Ingestion Pipeline — Sync repository metadata, text chunks, and vector embeddings."
    )
    parser.add_argument(
        "--repo",
        type=str,
        default="fastapi/fastapi",
        help="GitHub Repository target (default: fastapi/fastapi)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-chunking and re-embedding all documents regardless of content hash match."
    )
    parser.add_argument(
        "--qdrant-path",
        type=str,
        default="data/qdrant_db",
        help="Path to local Qdrant database storage directory (default: data/qdrant_db)"
    )
    
    args = parser.parse_args()
    
    print("=========================================")
    print("RepoMind RAG Master Sync Pipeline Runner")
    print("=========================================")
    print(f"Target Repository: {args.repo}")
    print(f"Force Mode:        {args.force}")
    print(f"Qdrant DB Path:    {args.qdrant_path}\n")
    
    pipeline = SyncPipeline(qdrant_path=args.qdrant_path)
    summary = pipeline.sync_repository(repo=args.repo, force=args.force)
    
    print("[SUCCESS] Master Repository Sync Completed Successfully!")

if __name__ == "__main__":
    main()
