import os
import shutil
from pathlib import Path
from typing import List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from groq import Groq
from config import config
from rag import retrieve_context
from pdf_ingestion import (
    ingest_pdf, 
    delete_pdf_from_kb, 
    list_ingested_pdfs,
    rebuild_entire_kb_from_pdfs
)
import io

# Validate configuration on startup
config.validate()

app = FastAPI(title="Portfolio RAG Voice Agent API")

# Create upload directory if it doesn't exist
UPLOAD_DIR = Path(config.UPLOAD_FOLDER)
UPLOAD_DIR.mkdir(exist_ok=True)

# Allow your frontend domain to call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

groq_client = Groq(api_key=config.GROQ_API_KEY)


@app.post("/chat")
async def chat(message: str = Form(...)):
    # Retrieve context with debug info
    context = retrieve_context(message, top_k=config.RETRIEVAL_TOP_K)
    
    # Debug: Log what was retrieved
    print(f"\n🔍 Query: {message}")
    print(f"📄 Retrieved context length: {len(context)} characters")
    print(f"📝 Context preview: {context[:200]}...")
    
    if not context or len(context) < 10:
        return {
            "answer": "I don't have any information in my knowledge base yet. Please upload some PDFs first!",
            "debug": {
                "query": message,
                "context_found": False,
                "context_length": 0
            }
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


@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()
    transcription = groq_client.audio.transcriptions.create(
        file=(audio.filename, audio_bytes),
        model=config.STT_MODEL,
    )
    return {"text": transcription.text}



@app.get("/health")
async def health():
    return {"status": "ok"}


# ============================================
# PDF UPLOAD & MANAGEMENT ENDPOINTS
# ============================================

@app.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    chunk_size: int = Form(400),
    overlap: int = Form(50),
    use_smart_chunking: bool = Form(True)
):
    """
    Upload a PDF file and ingest it into the knowledge base.
    
    Parameters:
    - file: PDF file to upload
    - chunk_size: Size of text chunks (default: 400 words)
    - overlap: Overlap between chunks (default: 50 words)
    - use_smart_chunking: Use intelligent chunking (default: True)
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save uploaded file
    file_path = UPLOAD_DIR / file.filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Ingest the PDF
        result = ingest_pdf(
            str(file_path),
            file.filename,
            chunk_size=chunk_size,
            overlap=overlap,
            use_smart_chunking=use_smart_chunking
        )
        
        return JSONResponse(content=result)
    
    except Exception as e:
        # Clean up file if ingestion fails
        if file_path.exists():
            file_path.unlink()
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Failed to process PDF: {str(e)}",
                "filename": file.filename
            }
        )


@app.post("/upload-multiple-pdfs")
async def upload_multiple_pdfs(
    files: List[UploadFile] = File(...),
    chunk_size: int = Form(400),
    overlap: int = Form(50)
):
    """
    Upload multiple PDF files at once.
    """
    results = []
    
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": "Not a PDF file"
            })
            continue
        
        file_path = UPLOAD_DIR / file.filename
        
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            result = ingest_pdf(
                str(file_path),
                file.filename,
                chunk_size=chunk_size,
                overlap=overlap
            )
            results.append(result)
        
        except Exception as e:
            if file_path.exists():
                file_path.unlink()
            
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": str(e)
            })
    
    successful = sum(1 for r in results if r.get("status") == "success")
    
    return {
        "total_files": len(files),
        "successful": successful,
        "failed": len(files) - successful,
        "details": results
    }


@app.get("/list-pdfs")
async def list_pdfs():
    """
    List all PDFs currently in the knowledge base.
    """
    pdfs = list_ingested_pdfs()
    return {
        "total_pdfs": len(pdfs),
        "pdfs": pdfs
    }


@app.delete("/delete-pdf/{filename}")
async def delete_pdf(filename: str):
    """
    Delete a specific PDF from the knowledge base.
    """
    result = delete_pdf_from_kb(filename)
    
    # Also delete the physical file if it exists
    file_path = UPLOAD_DIR / filename
    if file_path.exists():
        file_path.unlink()
    
    return result


@app.post("/rebuild-kb")
async def rebuild_knowledge_base():
    """
    Rebuild the entire knowledge base from all PDFs in the upload directory.
    WARNING: This will clear the existing knowledge base!
    """
    result = rebuild_entire_kb_from_pdfs(str(UPLOAD_DIR))
    return result


@app.post("/clear-kb")
async def clear_knowledge_base():
    """
    DANGER: Clear the entire knowledge base.
    Use this to remove old markdown data and start fresh.
    """
    from vector_store import get_client
    
    try:
        client = get_client()
        
        # Delete collection
        client.delete_collection(name="portfolio_kb")
        print("🗑️  Deleted existing collection")
        
        # Create fresh empty collection
        collection = client.create_collection(name="portfolio_kb")
        print("✅ Created fresh empty collection")
        
        count = collection.count()
        
        return {
            "status": "success",
            "message": "Knowledge base cleared successfully",
            "current_count": count
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/kb-stats")
async def get_kb_stats():
    """
    Get statistics about the knowledge base.
    """
    from rag import get_collection_stats
    
    try:
        stats = get_collection_stats()
        
        # Add debug info
        print(f"\n📊 Knowledge Base Stats:")
        print(f"   Total chunks: {stats.get('total_chunks', 0)}")
        print(f"   Total documents: {stats.get('total_documents', 0)}")
        print(f"   Documents: {stats.get('documents', {})}")
        
        return stats
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/debug-collection")
async def debug_collection():
    """
    Debug endpoint to check collection contents.
    """
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
        return {
            "error": str(e)
        }
