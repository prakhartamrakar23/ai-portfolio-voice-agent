"""
Shared vector store instance to ensure PDF ingestion and RAG retrieval 
use the SAME ChromaDB collection.

All initialization is LAZY — nothing loads until first use.
"""

# Global instances — only populated on first access
_model = None
_client = None
_collection = None


def get_model():
    """Get or create the embedding model (lazy singleton)."""
    global _model
    if _model is None:
        print("🔄 Loading embedding model...")
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Embedding model loaded")
    return _model


def get_client():
    """Get or create the ChromaDB client (lazy singleton)."""
    global _client
    if _client is None:
        print("🔄 Connecting to ChromaDB...")
        import chromadb
        _client = chromadb.PersistentClient(path="./chroma_db")
        print("✅ ChromaDB connected")
    return _client


def get_collection():
    """Get or create the portfolio_kb collection (lazy singleton)."""
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
    except Exception:
        pass
    _collection = client.create_collection(name="portfolio_kb")
    print("✅ Created fresh collection")
    return _collection