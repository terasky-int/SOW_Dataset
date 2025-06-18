import argparse
from database_manager import ChromaDBManager

def list_collections(list_docs=False):
    """
    List all collections in ChromaDB with their details
    
    Args:
        list_docs: Whether to list document names in each collection
    """
    db_manager = ChromaDBManager()
    
    # Get all collections
    collections = db_manager.get_all_collections()
    
    print(f"Found {len(collections)} collections:")
    for collection in collections:
        print(f"- {collection.name}")
        # Get collection
        coll = db_manager.create_collection(collection.name)
        count = coll.count()
        print(f"  Documents: {count}")
        
        # List document names if requested
        if list_docs and count > 0:
            print("  Document names:")
            all_docs = coll.get()
            for i, metadata in enumerate(all_docs["metadatas"]):
                file_name = metadata.get("file_name", "")
                if not file_name and "source" in metadata:
                    import os
                    file_name = os.path.basename(metadata["source"])
                doc_id = all_docs["ids"][i]
                print(f"    - {file_name or doc_id}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List ChromaDB collections")
    parser.add_argument("--list_docs", action="store_true", help="List document names in each collection")
    args = parser.parse_args()
    
    list_collections(args.list_docs)