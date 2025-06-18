from database_manager import ChromaDBManager

def list_collections():
    """
    List all collections in ChromaDB with their details
    """
    db_manager = ChromaDBManager()
    
    # Get all collections
    collections = db_manager.get_all_collections()
    
    print(f"Found {len(collections)} collections:")
    for collection in collections:
        print(f"- {collection.name}")
        # Optionally get collection count
        coll = db_manager.create_collection(collection.name)
        count = coll.count()
        print(f"  Documents: {count}")

if __name__ == "__main__":
    list_collections()
