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

    Returns a shim with full sentence-transformers .encode() API compatibility:
      - Accepts all keyword args (show_progress_bar, batch_size, convert_to_numpy, etc.)
      - .encode(texts).tolist()        → List[List[float]]  (used by rag.py)
      - .encode(texts)                 → behaves like np.ndarray (used by pdf_ingestion.py)
      - Iterating over result          → yields per-vector numpy arrays
    """
    global _model
    if _model is None:
        print("🔄 Loading embedding model (fastembed)...")
        from fastembed import TextEmbedding

        _fastembed = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

        class _EmbedResult:
            """
            Wraps the list of numpy vectors so it behaves like sentence-transformers output.
            Supports: .tolist(), iteration, indexing, and direct use as List[List[float]].
            """
            def __init__(self, vectors):
                self._vectors = vectors  # List[np.ndarray]

            def tolist(self):
                """rag.py pattern: model.encode([query]).tolist()"""
                return [v.tolist() for v in self._vectors]

            def __iter__(self):
                """pdf_ingestion pattern: for emb in model.encode(chunks)"""
                return iter(self._vectors)

            def __len__(self):
                return len(self._vectors)

            def __getitem__(self, idx):
                return self._vectors[idx]

            def __array__(self, dtype=None):
                """numpy interop: np.array(result) works correctly"""
                import numpy as np
                arr = np.array([v for v in self._vectors])
                return arr.astype(dtype) if dtype else arr

        class _EmbedShim:
            """
            Drop-in replacement for SentenceTransformer.
            Accepts all keyword args sentence-transformers supports and ignores unused ones.
            """
            def encode(self, texts, batch_size=32, show_progress_bar=False,
                       output_value='sentence_embedding', convert_to_numpy=True,
                       convert_to_tensor=False, device=None, normalize_embeddings=False,
                       **kwargs):
                vectors = list(_fastembed.embed(texts))  # generator → List[np.ndarray]
                return _EmbedResult(vectors)

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