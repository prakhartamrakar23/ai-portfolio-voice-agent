import os
import re
from typing import List, Dict
import pdfplumber
from datetime import datetime
from vector_store import get_model, get_collection, get_client, reset_collection

# Use shared instances
model = get_model()
collection = get_collection()

def clean_text(text: str) -> str:
    """Clean extracted PDF text."""
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    # Remove multiple newlines
    text = re.sub(r'\n+', '\n', text)
    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s\.,!?;:()\-]', '', text)
    return text.strip()

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using pdfplumber."""
    text_content = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    text_content.append(f"--- Page {page_num} ---\n{text}")
        
        full_text = "\n\n".join(text_content)
        return clean_text(full_text)
    
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    i = 0
    
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():  # Only add non-empty chunks
            chunks.append(chunk)
        i += chunk_size - overlap
    
    return chunks

def smart_chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[Dict[str, str]]:
    """
    Intelligently chunk text by trying to preserve semantic boundaries.
    Returns chunks with metadata about their content.
    """
    # Try to split on section headers first (lines with all caps, or starting with #)
    sections = re.split(r'\n(?=[A-Z\s]{3,}|#+\s)', text)
    
    all_chunks = []
    
    for section in sections:
        if not section.strip():
            continue
        
        # Get section title (first line)
        lines = section.split('\n')
        title = lines[0].strip() if lines else "Untitled Section"
        
        # Chunk the section
        section_chunks = chunk_text(section, chunk_size, overlap)
        
        for chunk in section_chunks:
            all_chunks.append({
                "text": chunk,
                "section": title[:100]  # Limit title length
            })
    
    return all_chunks if all_chunks else [{"text": text, "section": "Main Content"}]

def ingest_pdf(
    pdf_path: str, 
    filename: str,
    chunk_size: int = 400,
    overlap: int = 50,
    use_smart_chunking: bool = True
) -> Dict[str, any]:
    """
    Ingest a PDF file into the knowledge base.
    Returns statistics about the ingestion.
    """
    print(f"\n📄 Processing PDF: {filename}")
    
    # Extract text
    text = extract_text_from_pdf(pdf_path)
    
    if not text or len(text) < 50:
        return {
            "status": "error",
            "message": "Could not extract meaningful text from PDF",
            "filename": filename
        }
    
    print(f"✅ Extracted {len(text)} characters")
    
    # Chunk text
    if use_smart_chunking:
        chunks_data = smart_chunk_text(text, chunk_size, overlap)
        chunks = [c["text"] for c in chunks_data]
        sections = [c["section"] for c in chunks_data]
    else:
        chunks = chunk_text(text, chunk_size, overlap)
        sections = ["Main Content"] * len(chunks)
    
    print(f"✅ Created {len(chunks)} chunks")
    
    # Generate embeddings
    print("🔄 Generating embeddings...")
    embeddings = model.encode(chunks, show_progress_bar=True).tolist()
    print("✅ Embeddings generated")
    
    # Prepare metadata
    timestamp = datetime.now().isoformat()
    doc_ids = [f"{filename}_{i}_{timestamp}" for i in range(len(chunks))]
    metadatas = [
        {
            "source": filename,
            "chunk_index": i,
            "section": sections[i],
            "timestamp": timestamp,
            "type": "pdf"
        }
        for i in range(len(chunks))
    ]
    
    # Store in ChromaDB
    print("🔄 Storing in vector database...")
    collection.add(
        ids=doc_ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas
    )
    
    print(f"✅ Successfully ingested {filename}")
    
    return {
        "status": "success",
        "filename": filename,
        "chunks_created": len(chunks),
        "characters_processed": len(text),
        "timestamp": timestamp
    }

def delete_pdf_from_kb(filename: str) -> Dict[str, any]:
    """Delete all chunks from a specific PDF file."""
    try:
        # Get all items
        results = collection.get()
        
        # Find IDs that match this filename
        ids_to_delete = [
            doc_id for doc_id, metadata in zip(results["ids"], results["metadatas"])
            if metadata.get("source") == filename
        ]
        
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            return {
                "status": "success",
                "message": f"Deleted {len(ids_to_delete)} chunks from {filename}",
                "chunks_deleted": len(ids_to_delete)
            }
        else:
            return {
                "status": "error",
                "message": f"No chunks found for {filename}"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def list_ingested_pdfs() -> List[Dict[str, any]]:
    """List all PDFs currently in the knowledge base."""
    try:
        results = collection.get()
        
        # Group by source filename
        pdf_stats = {}
        for metadata in results["metadatas"]:
            source = metadata.get("source", "unknown")
            if metadata.get("type") == "pdf":
                if source not in pdf_stats:
                    pdf_stats[source] = {
                        "filename": source,
                        "chunk_count": 0,
                        "last_updated": metadata.get("timestamp", "unknown")
                    }
                pdf_stats[source]["chunk_count"] += 1
        
        return list(pdf_stats.values())
    
    except Exception as e:
        print(f"Error listing PDFs: {e}")
        return []

def rebuild_entire_kb_from_pdfs(pdf_directory: str = "./uploaded_pdfs") -> Dict[str, any]:
    """
    Rebuild the entire knowledge base from all PDFs in a directory.
    Useful for batch processing or resetting the KB.
    """
    global collection
    
    if not os.path.exists(pdf_directory):
        return {
            "status": "error",
            "message": f"Directory {pdf_directory} does not exist"
        }
    
    # Clear existing collection using shared reset function
    collection = reset_collection()
    
    # Process all PDFs
    pdf_files = [f for f in os.listdir(pdf_directory) if f.lower().endswith('.pdf')]
    
    if len(pdf_files) == 0:
        return {
            "status": "error",
            "message": f"No PDF files found in {pdf_directory}"
        }
    
    results = []
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_directory, pdf_file)
        result = ingest_pdf(pdf_path, pdf_file)
        results.append(result)
    
    successful = sum(1 for r in results if r["status"] == "success")
    
    return {
        "status": "success",
        "total_pdfs": len(pdf_files),
        "successful": successful,
        "failed": len(pdf_files) - successful,
        "details": results
    }

if __name__ == "__main__":
    # Test with a sample PDF
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        if os.path.exists(pdf_path):
            result = ingest_pdf(pdf_path, os.path.basename(pdf_path))
            print("\n" + "="*50)
            print("INGESTION RESULT:")
            print("="*50)
            for key, value in result.items():
                print(f"{key}: {value}")
        else:
            print(f"Error: File {pdf_path} not found")
    else:
        print("Usage: python pdf_ingestion.py <path_to_pdf>")
        print("\nOr use the /upload API endpoint")
