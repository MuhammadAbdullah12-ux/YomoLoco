import os
import sys
import json
import time


# Add project root directory to sys.path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Set PyTorch thread limit to prevent deadlocks
import torch
torch.set_num_threads(1)

from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from ingestion.ask_pipeline import AskPipeline

# 1. Define the LLM Judge Structured Response Schema
class FaithfulnessJudgeSchema(BaseModel):
    faithful: bool = Field(
        description="True if the generated answer relies ONLY on the provided context without any outside information, assumptions, or hallucinations. False otherwise."
    )
    reasoning: str = Field(
        description="A concise one-sentence reasoning explaining the verdict based on the context and answer."
    )
    completeness: int = Field(
        description="Score from 1 to 5 indicating how completely the answer covers the information required to answer the question, based on the provided context (1 = completely incomplete, 5 = fully complete)."
    )

def safe_print(text: str):
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or 'utf-8'
        print(text.encode(encoding, errors='replace').decode(encoding))

def run_faithfulness_judge():
    print("==================================================")
    print("Task 1 & 2: Day 2 Faithfulness & LLM-as-Judge Eval")
    print("==================================================")
    
    # Check Gemini API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_key_here":
        print("[ERROR] GEMINI_API_KEY is not configured or is the default placeholder.")
        print("Please configure a valid GEMINI_API_KEY in your .env file to run LLM-as-Judge evaluation.")
        sys.exit(1)
        
    eval_path = "eval/questions.json"
    report_path = "eval/faithfulness_report.json"
    
    if not os.path.exists(eval_path):
        print(f"[ERROR] Evaluation questions file '{eval_path}' not found.")
        sys.exit(1)
        
    with open(eval_path, "r", encoding="utf-8") as f:
        questions = json.load(f)
        
    print(f"Loaded {len(questions)} evaluation questions.")
    
    # 2. Initialize RAG AskPipeline
    print("[RUNNING] Initializing RAG AskPipeline...")
    qdrant_path = "data/qdrant_db"

    pipeline = AskPipeline(qdrant_path=qdrant_path)

    
    # 3. Initialize Gemini Judge client
    print("[RUNNING] Initializing Gemini Judge client...")
    judge_client = genai.Client()
    judge_model = "gemini-flash-latest"


    
    report_records = []
    
    for idx, q in enumerate(questions, 1):
        query = q.get("question", "")
        category = q.get("category", "general")
        print(f"\n--- Question #{idx:02d}: \"{query}\" ---")
        
        # Run RAG pipeline to get answer and source chunks
        try:
            rag_response = pipeline.ask(query)
            rag_answer = rag_response.get("answer", "")
            source_chunks = rag_response.get("source_chunks", [])
        except Exception as e:
            print(f"  [ERROR] RAG generation failed for this query: {e}")
            continue
            
        # Format candidate context chunks for the judge
        chunks_str_list = []
        for c_idx, cand in enumerate(source_chunks, 1):
            chunk_id = cand.get("chunk_id") or cand.get("id") or "N/A"
            text = cand.get("text") or cand.get("content") or ""
            chunks_str_list.append(f"--- Chunk #{c_idx} (ID: {chunk_id}) ---\n{text.strip()}\n")
        context_block = "\n".join(chunks_str_list)
        
        # Construct the Judge Evaluation Prompt
        judge_prompt = (
            "You are an expert independent QA judge. Your task is to evaluate the quality of a generated answer from a RAG system.\n"
            "Analyze the provided context chunks and compare them strictly against the generated answer.\n\n"
            "=========================================\n"
            "RETRIEVED CONTEXT CHUNKS:\n"
            f"{context_block}\n"
            "=========================================\n\n"
            f"USER QUESTION: {query}\n"
            f"GENERATED RAG ANSWER: {rag_answer}\n\n"
            "Evaluate:\n"
            "1. Faithfulness: Is the RAG answer fully supported by the retrieved context chunks without any outside knowledge or extrapolation?\n"
            "2. Completeness: Score from 1 to 5 how fully the RAG answer addresses the user question based on the retrieved context."
        )
        
        # Call Gemini Judge with structured schema config
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=FaithfulnessJudgeSchema,
            temperature=0.0
        )
        
        try:
            print("  [RUNNING] Querying LLM-as-Judge...")
            response = judge_client.models.generate_content(
                model=judge_model,
                contents=judge_prompt,
                config=config
            )
            
            judge_result = json.loads(response.text)
            print(f"  [SUCCESS] Judge Verdict: Faithful={judge_result['faithful']}, Completeness={judge_result['completeness']}/5")
            print(f"  Reasoning: {judge_result['reasoning']}")
            
            report_records.append({
                "query_number": idx,
                "category": category,
                "question": query,
                "rag_answer": rag_answer,
                "judge_verdict": {
                    "faithful": judge_result["faithful"],
                    "completeness": judge_result["completeness"],
                    "reasoning": judge_result["reasoning"]
                }
            })
        except Exception as je:
            print(f"  [ERROR] Judge call failed: {je}")
            
        # Space out requests to avoid free tier rate limits (15 RPM)
        time.sleep(5)

            
    pipeline.close()

    # Save findings

    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as rf:
        json.dump(report_records, rf, indent=2, ensure_ascii=False)
        
    print(f"\n==================================================")
    print(f"[SUCCESS] Evaluation finished. Report exported to '{report_path}'")
    print("==================================================")

if __name__ == "__main__":
    run_faithfulness_judge()
