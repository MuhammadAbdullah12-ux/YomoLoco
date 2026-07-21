import os
import sys
import json
import hashlib
from datetime import datetime
from typing import Optional

from sqlmodel import Session, select
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from backend.database import init_db, engine
from backend.models import DocumentRecord, ChunkRecord, SyncLogRecord
from ingestion.embedder import TextEmbedder
from ingestion.splitter import split_readme, split_text_by_length

# Safe print helper for Windows consoles
def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or 'utf-8'
        print(text.encode(encoding, errors='replace').decode(encoding))

class SyncPipeline:
    """
    Master Ingestion Orchestrator.
    Wires together raw document ingestion, SHA-256 mutation diffing,
    Markdown/length text splitters, TextEmbedder, Qdrant vector storage,
    and SQLModel relational metadata storage.
    """
    def __init__(
        self,
        qdrant_path: str = "data/qdrant_db",
        collection_name: str = "repomind_collection"
    ):
        self.qdrant_path = qdrant_path
        self.collection_name = collection_name
        
        # 1. Ensure SQLModel tables exist
        init_db()
        
        # 2. Instantiate TextEmbedder
        self.embedder = TextEmbedder()
        
        # 3. Initialize local Qdrant engine
        print(f"[RUNNING] Connecting to local Qdrant engine at '{self.qdrant_path}'...")
        self.qdrant = QdrantClient(path=self.qdrant_path)
        
        # 4. Setup collection if missing
        try:
            if not self.qdrant.collection_exists(self.collection_name):
                print(f"[RUNNING] Creating collection '{self.collection_name}' with 384 dimensions...")
                self.qdrant.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                )
        except Exception:
            pass
        print(f"[SUCCESS] Pipeline ready with Qdrant collection '{self.collection_name}'.")

    def close(self):
        """
        Closes connection to Qdrant local storage to release file locks.
        """
        try:
            if hasattr(self, "qdrant") and self.qdrant:
                self.qdrant.close()
        except Exception:
            pass

    @staticmethod
    def compute_content_hash(text: str) -> str:
        """
        Computes SHA-256 hash string for raw text content.
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def sync_repository(self, repo: str = "fastapi/fastapi", force: bool = False) -> dict:
        """
        Executes a full repository sync pass with differential update detection.
        """
        print(f"\n=========================================")
        print(f"Starting Master Sync Pipeline for: '{repo}'")
        print(f"=========================================")
        
        readme_path = "data/raw/readme.json"
        issues_path = "data/raw/issues.json"
        
        docs_to_process = []
        
        # Load README
        if os.path.exists(readme_path):
            with open(readme_path, "r", encoding="utf-8") as f:
                readme_data = json.load(f)
            docs_to_process.append({
                "doc_id": f"readme-{repo}",
                "doc_type": "readme",
                "title": "README.md",
                "content": readme_data.get("body") or readme_data.get("content") or "",
                "url": f"https://github.com/{repo}/blob/main/README.md",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            
        # Load Issues & PRs
        if os.path.exists(issues_path):
            with open(issues_path, "r", encoding="utf-8") as f:
                issues_data = json.load(f)
            for idx, item in enumerate(issues_data):
                doc_id = item.get("doc_id") or f"issue-{item.get('number', idx)}"
                doc_type = item.get("doc_type") or ("pr" if "pull_request" in item or item.get("html_url", "").find("/pull/") != -1 else "issue")
                title = item.get("title", "")
                body = item.get("body", "") or ""
                content = body if body.startswith("Title:") else f"Title: {title}\nDescription: {body}"
                
                c_at_str = item.get("created_at")
                c_at = datetime.fromisoformat(c_at_str.replace("Z", "+00:00")) if c_at_str else datetime.utcnow()
                u_at_str = item.get("updated_at")
                u_at = datetime.fromisoformat(u_at_str.replace("Z", "+00:00")) if u_at_str else datetime.utcnow()
                
                docs_to_process.append({
                    "doc_id": doc_id,
                    "doc_type": doc_type,
                    "title": title,
                    "content": content,
                    "url": item.get("url") or item.get("html_url") or f"https://github.com/{repo}/issues/{doc_id.split('-')[-1]}",
                    "created_at": c_at,
                    "updated_at": u_at
                })

        print(f"Loaded {len(docs_to_process)} raw documents to inspect.")
        
        docs_added = 0
        docs_updated = 0
        docs_skipped = 0
        total_chunks_created = 0
        
        with Session(engine) as session:
            for item in docs_to_process:
                doc_id = item["doc_id"]
                content = item["content"]
                c_hash = self.compute_content_hash(content)
                
                existing_doc = session.get(DocumentRecord, doc_id)
                
                # Check for unchanged document
                if existing_doc and existing_doc.content_hash == c_hash and not force:
                    docs_skipped += 1
                    continue
                    
                # Handle updated document (clean up stale chunks)
                if existing_doc and (existing_doc.content_hash != c_hash or force):
                    safe_print(f"  [MUTATION DETECTED] Updating document: {doc_id}")
                    # Find old chunk records
                    old_chunks = session.exec(select(ChunkRecord).where(ChunkRecord.doc_id == doc_id)).all()
                    if old_chunks:
                        point_ids = [c.qdrant_point_id for c in old_chunks]
                        try:
                            self.qdrant.delete(collection_name=self.collection_name, points_selector=point_ids)
                        except Exception:
                            pass
                        for c in old_chunks:
                            session.delete(c)
                    existing_doc.content_hash = c_hash
                    existing_doc.updated_at = item["updated_at"]
                    session.add(existing_doc)
                    docs_updated += 1
                else:
                    safe_print(f"  [NEW DOCUMENT] Adding document: {doc_id}")
                    new_doc = DocumentRecord(
                        doc_id=doc_id,
                        doc_type=item["doc_type"],
                        repo=repo,
                        title=item["title"],
                        created_at=item["created_at"],
                        updated_at=item["updated_at"],
                        url=item["url"],
                        content_hash=c_hash
                    )
                    session.add(new_doc)
                    docs_added += 1
                    
                # Chunk text
                if item["doc_type"] == "readme":
                    chunks_text = split_readme(content)
                else:
                    chunks_text = split_text_by_length(content)
                    
                if not chunks_text:
                    continue
                    
                # Embed chunks & build Qdrant points
                vectors = self.embedder.embed_chunks(chunks_text)
                points_buffer = []
                
                for pos, (chunk_str, vector) in enumerate(zip(chunks_text, vectors)):
                    chunk_id = f"{doc_id}-chunk-{pos}"
                    # Generate deterministic integer point ID for Qdrant
                    qdrant_point_id = abs(hash(chunk_id)) % (2**63 - 1)
                    
                    points_buffer.append(PointStruct(
                        id=qdrant_point_id,
                        vector=vector,
                        payload={
                            "doc_id": doc_id,
                            "chunk_id": chunk_id,
                            "doc_type": item["doc_type"],
                            "repo": repo,
                            "text": chunk_str,
                            "url": item["url"]
                        }
                    ))
                    
                    chunk_record = ChunkRecord(
                        chunk_id=chunk_id,
                        doc_id=doc_id,
                        position=pos,
                        text=chunk_str,
                        qdrant_point_id=qdrant_point_id
                    )
                    session.add(chunk_record)
                    total_chunks_created += 1
                    
                # Upsert points to Qdrant
                if points_buffer:
                    self.qdrant.upsert(
                        collection_name=self.collection_name,
                        wait=True,
                        points=points_buffer
                    )
                    
            # Record audit sync log
            sync_log = SyncLogRecord(
                repo=repo,
                last_synced_at=datetime.utcnow(),
                docs_added=docs_added,
                docs_updated=docs_updated
            )
            session.add(sync_log)
            session.commit()
            
        summary = {
            "status": "success",
            "repo": repo,
            "total_documents": len(docs_to_process),
            "docs_added": docs_added,
            "docs_updated": docs_updated,
            "docs_skipped": docs_skipped,
            "chunks_created": total_chunks_created
        }
        
        print("\n-----------------------------------------")
        print("Master Ingestion Sync Completed Summary:")
        print(f"  - Total Documents Examined: {summary['total_documents']}")
        print(f"  - Documents Added:           {summary['docs_added']}")
        print(f"  - Documents Updated:         {summary['docs_updated']}")
        print(f"  - Documents Skipped:         {summary['docs_skipped']}")
        print(f"  - Chunks Created & Upserted: {summary['chunks_created']}")
        print("-----------------------------------------\n")
        
        return summary
