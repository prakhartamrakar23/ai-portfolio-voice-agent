"""
Clear the knowledge base completely.
Use this to remove old markdown data and start fresh with PDFs only.
"""
from vector_store import get_client

def clear_knowledge_base():
    print("\n" + "="*60)
    print("CLEARING KNOWLEDGE BASE")
    print("="*60)
    
    client = get_client()
    
    try:
        # Delete the collection
        client.delete_collection(name="portfolio_kb")
        print("\n✅ Deleted existing 'portfolio_kb' collection")
        
        # Recreate empty collection
        collection = client.create_collection(name="portfolio_kb")
        print("✅ Created fresh empty collection")
        
        # Verify it's empty
        count = collection.count()
        print(f"✅ Current count: {count} (should be 0)")
        
        print("\n" + "="*60)
        print("✅ KNOWLEDGE BASE CLEARED SUCCESSFULLY")
        print("="*60)
        print("\nNext steps:")
        print("1. Upload your PDF files via the API or web UI")
        print("2. Test the voice agent with your PDF content")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    # Require confirmation
    if len(sys.argv) > 1 and sys.argv[1] == "--confirm":
        clear_knowledge_base()
    else:
        print("\n⚠️  WARNING: This will DELETE all data from the knowledge base!")
        print("\nTo confirm, run:")
        print("    python clear_kb.py --confirm")
