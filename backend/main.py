from fastapi import FastAPI

app = FastAPI(
    title="RepoMind API",
    description="AI assistant backend for repository search and semantic RAG.",
    version="0.1.0"
)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "repomind-backend"
    }
