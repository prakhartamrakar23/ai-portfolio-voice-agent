"""
Shared vector store instance to ensure PDF ingestion and RAG retrieval 
use the SAME ChromaDB collection.
"""
from sentence_transformers import SentenceTransformer
import chromadb

# Global instances - shared across all modules
_model = None
_client = None
_collection = None

def get_model():
    """Get or create the embedding model (singleton)."""
    global _model
    if _model is None:
        print("🔄 Loading embedding model...")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Embedding model loaded")
    return _model

def get_client():
    """Get or create the ChromaDB client (singleton)."""
    global _client
    if _client is None:
        print("🔄 Connecting to ChromaDB...")
        _client = chromadb.PersistentClient(path="./chroma_db")
        print("✅ ChromaDB connected")
    return _client

def get_collection():
    """Get or create the portfolio_kb collection (singleton)."""
    global _collection
    if _collection is None:
        client = get_client()
        print("🔄 Getting collection 'portfolio_kb'...")
        _collection = client.get_or_create_collection(name="portfolio_kb")
        print("✅ Collection ready")
    return _collection

def reset_collection():
    """Delete and recreate the collection (for rebuild operations)."""
    global _collection
    client = get_client()
    try:
        client.delete_collection(name="portfolio_kb")
        print("🗑️  Deleted existing collection")
    except:
        pass
    _collection = client.create_collection(name="portfolio_kb")
    print("✅ Created fresh collection")
    return _collection
