from typing import Dict
from vector_store import get_model, get_collection

# ⚠️  DO NOT call get_model() or get_collection() here at module level.
# They are called lazily inside each function, so nothing loads on import.


def retrieve_context(query: str, top_k: int = 5) -> str:
    """
    Retrieve relevant context for a query.
    Model and collection are loaded on first call, not on import.
    """
    model = get_model()
    collection = get_collection()

    query_embedding = model.encode([query]).tolist()

    try:
        count_result = collection.count()
        print(f"📊 Collection has {count_result} items")

        if count_result == 0:
            print("⚠️  Collection is empty! Please upload PDFs first.")
            return ""
    except Exception as e:
        print(f"❌ Error checking collection: {e}")
        return ""

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(top_k, count_result)
    )

    if not results["documents"] or len(results["documents"][0]) == 0:
        print("⚠️  No matching documents found!")
        return ""

    chunks = results["documents"][0]
    print(f"✅ Retrieved {len(chunks)} chunks")

    return "\n\n---\n\n".join(chunks)


def retrieve_context_with_metadata(query: str, top_k: int = 3) -> Dict:
    """
    Retrieve context with metadata about sources.
    """
    model = get_model()
    collection = get_collection()

    query_embedding = model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )

    return {
        "chunks": results["documents"][0],
        "metadatas": results["metadatas"][0] if results["metadatas"] else [],
        "distances": results["distances"][0] if results["distances"] else []
    }


def get_collection_stats() -> Dict:
    """
    Get statistics about the knowledge base collection.
    """
    try:
        collection = get_collection()
        results = collection.get()

        total_chunks = len(results["ids"])

        sources = {}
        for metadata in results["metadatas"]:
            source = metadata.get("source", "unknown")
            doc_type = metadata.get("type", "markdown")

            if source not in sources:
                sources[source] = {"type": doc_type, "chunk_count": 0}
            sources[source]["chunk_count"] += 1

        return {
            "total_chunks": total_chunks,
            "total_documents": len(sources),
            "documents": sources,
            "status": "healthy"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "total_chunks": 0,
            "total_documents": 0
        }