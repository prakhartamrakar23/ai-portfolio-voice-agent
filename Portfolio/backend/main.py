import os
import shutil
from pathlib import Path
from typing import List
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from groq import Groq
from config import config
from rag import retrieve_context
from pdf_ingestion import (
    ingest_pdf,
    delete_pdf_from_kb,
    list_ingested_pdfs,
    rebuild_entire_kb_from_pdfs
)

# ── Startup: warm up model + DB so first /chat request isn't slow ──────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the embedding model and connect ChromaDB at startup."""
    print("🚀 Warming up model and vector store...")
    try:
        from vector_store import get_model, get_collection
        get_model()        # ~200 MB, loads once
        get_collection()   # connects ChromaDB
        print("✅ Warm-up complete — ready to serve requests")
    except Exception as e:
        print(f"⚠️  Warm-up failed (non-fatal): {e}")
    yield
    # shutdown logic (if any) goes here

# ── App ────────────────────────────────────────────────────────────────────────
config.validate()

app = FastAPI(title="Portfolio RAG Voice Agent API", lifespan=lifespan)

UPLOAD_DIR = Path(config.UPLOAD_FOLDER)
UPLOAD_DIR.mkdir(exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

groq_client = Groq(api_key=config.GROQ_API_KEY)


# ── Chat ───────────────────────────────────────────────────────────────────────
@app.post("/chat")
async def chat(message: str = Form(...)):
    try:
        context = retrieve_context(message, top_k=config.RETRIEVAL_TOP_K)

        print(f"\n🔍 Query: {message}")
        print(f"📄 Context length: {len(context)} chars")

        if not context or len(context) < 10:
            return {
                "answer": "I don't have any information in my knowledge base yet. Please upload some PDFs first!",
                "debug": {"query": message, "context_found": False, "context_length": 0}
            }

        prompt = config.SYSTEM_PROMPT.replace("{context}", context)

        response = groq_client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": message}
            ],
            temperature=config.LLM_TEMPERATURE,
            max_tokens=config.LLM_MAX_TOKENS
        )
        answer = response.choices[0].message.content

        return {
            "answer": answer,
            "debug": {
                "query": message,
                "context_found": True,
                "context_length": len(context),
                "chunks_retrieved": len(context.split("---"))
            }
        }
    except Exception as e:
        print(f"❌ /chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Transcribe ─────────────────────────────────────────────────────────────────
@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    try:
        audio_bytes = await audio.read()
        transcription = groq_client.audio.transcriptions.create(
            file=(audio.filename, audio_bytes),
            model=config.STT_MODEL,
        )
        return {"text": transcription.text}
    except Exception as e:
        print(f"❌ /transcribe error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}


# ── PDF management ─────────────────────────────────────────────────────────────
@app.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    chunk_size: int = Form(400),
    overlap: int = Form(50),
    use_smart_chunking: bool = Form(True)
):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    file_path = UPLOAD_DIR / file.filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = ingest_pdf(
            str(file_path),
            file.filename,
            chunk_size=chunk_size,
            overlap=overlap,
            use_smart_chunking=use_smart_chunking
        )
        return JSONResponse(content=result)

    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        print(f"❌ /upload-pdf error: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e), "filename": file.filename}
        )


@app.post("/upload-multiple-pdfs")
async def upload_multiple_pdfs(
    files: List[UploadFile] = File(...),
    chunk_size: int = Form(400),
    overlap: int = Form(50)
):
    results = []

    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            results.append({"filename": file.filename, "status": "error", "message": "Not a PDF file"})
            continue

        file_path = UPLOAD_DIR / file.filename
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            result = ingest_pdf(str(file_path), file.filename, chunk_size=chunk_size, overlap=overlap)
            results.append(result)
        except Exception as e:
            if file_path.exists():
                file_path.unlink()
            results.append({"filename": file.filename, "status": "error", "message": str(e)})

    successful = sum(1 for r in results if r.get("status") == "success")
    return {"total_files": len(files), "successful": successful, "failed": len(files) - successful, "details": results}


@app.get("/list-pdfs")
async def list_pdfs():
    pdfs = list_ingested_pdfs()
    return {"total_pdfs": len(pdfs), "pdfs": pdfs}


@app.delete("/delete-pdf/{filename}")
async def delete_pdf(filename: str):
    result = delete_pdf_from_kb(filename)
    file_path = UPLOAD_DIR / filename
    if file_path.exists():
        file_path.unlink()
    return result


@app.post("/rebuild-kb")
async def rebuild_knowledge_base():
    return rebuild_entire_kb_from_pdfs(str(UPLOAD_DIR))


@app.post("/clear-kb")
async def clear_knowledge_base():
    from vector_store import get_client
    try:
        client = get_client()
        client.delete_collection(name="portfolio_kb")
        collection = client.create_collection(name="portfolio_kb")
        return {"status": "success", "message": "Knowledge base cleared", "current_count": collection.count()}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/kb-stats")
async def get_kb_stats():
    from rag import get_collection_stats
    try:
        return get_collection_stats()
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/debug-collection")
async def debug_collection():
    from vector_store import get_collection
    try:
        collection = get_collection()
        results = collection.get()
        return {
            "total_items": len(results["ids"]),
            "sample_ids": results["ids"][:5] if results["ids"] else [],
            "sample_documents": results["documents"][:2] if results["documents"] else [],
            "sample_metadata": results["metadatas"][:5] if results["metadatas"] else []
        }
    except Exception as e:
        return {"error": str(e)}