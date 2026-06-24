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
    """Get or create the embedding model (lazy singleton).

    Uses fastembed (ONNX-based) instead of sentence-transformers (PyTorch-based).
    RAM usage: ~50MB vs ~500MB — safe for Render free tier (512MB limit).
    Model: BAAI/bge-small-en-v1.5 ≈ same accuracy as all-MiniLM-L6-v2.

    Returns a shim that exposes .encode(texts) -> object with .tolist(),
    so existing callers in rag.py need zero changes.
    """
    global _model
    if _model is None:
        print("🔄 Loading embedding model (fastembed)...")
        from fastembed import TextEmbedding

        _fastembed = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

        class _EmbedShim:
            """Drop-in shim: shim.encode(texts).tolist() mirrors sentence-transformers API."""
            def encode(self, texts):
                vectors = list(_fastembed.embed(texts))  # generator → list of np arrays

                class _Result:
                    def tolist(self_inner):
                        return [v.tolist() for v in vectors]

                return _Result()

        _model = _EmbedShim()
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