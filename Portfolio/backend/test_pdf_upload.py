"""
Test script to verify PDF upload and retrieval works correctly.
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vector_store import get_collection, get_model

def test_collection():
    print("\n" + "="*60)
    print("TESTING KNOWLEDGE BASE")
    print("="*60)
    
    # Get collection
    collection = get_collection()
    model = get_model()
    
    # Check count
    count = collection.count()
    print(f"\n✅ Collection item count: {count}")
    
    if count == 0:
        print("\n⚠️  WARNING: Collection is EMPTY!")
        print("   Please upload PDF files first using:")
        print("   1. The web UI: http://localhost:8000/upload.html")
        print("   2. Or the API: curl -X POST http://localhost:8000/upload-pdf -F 'file=@yourfile.pdf'")
        return False
    
    # Get sample data
    results = collection.get(limit=5)
    
    print(f"\n📄 Sample Documents:")
    print(f"   Total IDs: {len(results['ids'])}")
    
    if results['metadatas']:
        print(f"\n📋 Sample Metadata:")
        for i, metadata in enumerate(results['metadatas'][:3]):
            print(f"   {i+1}. Source: {metadata.get('source', 'unknown')}")
            print(f"      Type: {metadata.get('type', 'unknown')}")
            print(f"      Section: {metadata.get('section', 'unknown')[:50]}...")
    
    if results['documents']:
        print(f"\n📝 Sample Chunk (first 200 chars):")
        print(f"   {results['documents'][0][:200]}...")
    
    # Test retrieval
    print(f"\n🔍 Testing Retrieval...")
    test_queries = [
        "What are your skills?",
        "Tell me about your experience",
        "What projects have you worked on?"
    ]
    
    for query in test_queries:
        query_embedding = model.encode([query]).tolist()
        search_results = collection.query(
            query_embeddings=query_embedding,
            n_results=3
        )
        
        matches = len(search_results["documents"][0]) if search_results["documents"] else 0
        print(f"   Query: '{query}'")
        print(f"   ✅ Found {matches} matching chunks")
    
    print(f"\n{'='*60}")
    print("✅ ALL TESTS PASSED")
    print("="*60)
    return True

if __name__ == "__main__":
    try:
        test_collection()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
