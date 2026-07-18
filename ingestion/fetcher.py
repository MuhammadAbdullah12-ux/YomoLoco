import os
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
from github import Github

# ==========================================
# Task 2: Define the Document Schema
# ==========================================

class Document(BaseModel):
    """
    Standardized schema for all ingested repository records.
    Every document (README, Issue, or Pull Request) must match this structure.
    """
    doc_id: str                          # Unique identifier (e.g. "readme" or "issue-42")
    doc_type: Literal["readme", "issue", "pr"]  # Type of the source document
    repo: str                            # Full repository name (e.g. "fastapi/fastapi")
    title: str                           # Title of the document
    body: str                            # Main text content of the document
    author: str                          # GitHub username of the author
    created_at: datetime                 # Timestamp when created
    updated_at: datetime                 # Timestamp when last updated
    
# ==========================================
# Day 4 - Task 1: Build the Cleanup Utility (Noise Reduction)
# ==========================================
import re

# Set of automated system bot accounts to filter out
BOT_USERNAMES = {
    "dependabot[bot]",
    "codspeed-hq[bot]",
    "github-actions[bot]",
    "sonarcloud[bot]",
    "coveralls[bot]"
}

def clean_text(text: str) -> str:
    """
    Cleans raw Markdown/HTML text by removing comment wrappers and normalizing white space.
    """
    if not text:
        return ""
    # Strip HTML comments: <!-- comment -->
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # Remove excessive blank lines (3 or more) to clean up layout
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

# ==========================================
# Task 3: Implement README Fetching
# ==========================================

def fetch_readme(repo) -> Document:
    """
    Downloads and normalizes the repository README.md file.
    """
    print("[RUNNING] Fetching README.md...")
    try:
        # 1. Fetch the README metadata and content
        readme_file = repo.get_readme()
        
        # 2. Decode and clean the raw base64 content bytes to string
        body_text = clean_text(readme_file.decoded_content.decode("utf-8"))
        
        # 3. Create and return the standardized Document schema object
        return Document(
            doc_id=f"readme-{repo.full_name}",
            doc_type="readme",
            repo=repo.full_name,
            title=readme_file.name,
            body=body_text,
            author=repo.owner.login,
            created_at=repo.created_at,
            updated_at=repo.updated_at,
            url=readme_file.html_url
        )
    except Exception as e:
        print(f"[ERROR] Failed to fetch README.md: {str(e)}")
        raise e

# ==========================================
# Task 4: Implement Issues & Comments Fetching
# ==========================================

def fetch_issues(repo, limit: int = 50) -> list[Document]:
    """
    Downloads open issues (including comments and PRs) and normalizes them.
    """
    print(f"[RUNNING] Fetching up to {limit} open issues and PRs (with comments)...")
    documents = []
    
    try:
        # 1. Fetch open issues from the repository
        # (GitHub API returns PRs in this list too)
        issues = repo.get_issues(state="open")
        
        count = 0
        for issue in issues:
            if count >= limit:
                break
                
            # 2. Check if this is a Pull Request or a standard Issue
            is_pr = issue.pull_request is not None
            doc_type = "pr" if is_pr else "issue"
            doc_prefix = "pr" if is_pr else "issue"
            
            print(f"  -> Processing {doc_type} #{issue.number}...")
            
            # 3. Fetch and clean description, and extract human-only comments
            body_content = f"Title: {issue.title}\n\nDescription:\n{clean_text(issue.body or '')}\n"
            
            comments = issue.get_comments()
            if comments.totalCount > 0:
                comment_blocks = []
                for comment in comments:
                    # Skip automated system bots to reduce noise in RAG search
                    if comment.user.login in BOT_USERNAMES:
                        continue
                    
                    cleaned_comment = clean_text(comment.body or "")
                    if cleaned_comment:
                        comment_blocks.append(
                            f"\n--- Comment by {comment.user.login} on {comment.created_at} ---\n{cleaned_comment}\n"
                        )
                
                if comment_blocks:
                    body_content += "\nComments:\n" + "".join(comment_blocks)
            
            # 4. Standardize the issue/PR into a Document schema
            doc = Document(
                doc_id=f"{doc_prefix}-{issue.number}",
                doc_type=doc_type,
                repo=repo.full_name,
                title=issue.title,
                body=body_content,
                author=issue.user.login,
                created_at=issue.created_at,
                updated_at=issue.updated_at,
                url=issue.html_url
            )
            documents.append(doc)
            count += 1
            
        print(f"[SUCCESS] Fetched and normalized {len(documents)} issues/PRs.")
        return documents
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch issues: {str(e)}")
        raise e

# ==========================================
# Task 5: Main Execution and JSON Export
# ==========================================

if __name__ == "__main__":
    import json

    # 1. Load configuration settings
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPO")

    if not token or not repo_name:
        print("[ERROR] Please configure GITHUB_TOKEN and GITHUB_REPO in the .env file.")
        exit(1)

    print(f"Starting ingestion process for: {repo_name}...")

    try:
        # 2. Setup output folder
        output_dir = "data/raw"
        os.makedirs(output_dir, exist_ok=True)

        # 3. Connect to GitHub
        g = Github(token)
        repo = g.get_repo(repo_name)

        # 4. Fetch and save README
        readme_doc = fetch_readme(repo)
        
        # Pydantic v1 vs v2 compatibility helper
        readme_dict = readme_doc.dict() if hasattr(readme_doc, "dict") else readme_doc.model_dump()
        
        readme_path = os.path.join(output_dir, "readme.json")
        with open(readme_path, "w", encoding="utf-8") as f:
            json.dump(readme_dict, f, indent=2, default=str)
        print(f"[SUCCESS] Saved README to: {readme_path}")

        # 5. Fetch and save Issues (limit to 30 for fast testing)
        issue_docs = fetch_issues(repo, limit=30)
        
        issues_list = [
            doc.dict() if hasattr(doc, "dict") else doc.model_dump()
            for doc in issue_docs
        ]
        
        issues_path = os.path.join(output_dir, "issues.json")
        with open(issues_path, "w", encoding="utf-8") as f:
            json.dump(issues_list, f, indent=2, default=str)
        print(f"[SUCCESS] Saved {len(issues_list)} issues to: {issues_path}")

        print("\n--- Ingestion Day 4 Task Completed Successfully! ---")

    except Exception as e:
        print(f"\n[ERROR] Ingestion pipeline failed: {str(e)}")


