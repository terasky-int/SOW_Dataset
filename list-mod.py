import argparse
import os
from database_manager import ChromaDBManager

def list_collections(list_docs=False, show_metadata=False):
    """
    List all collections in ChromaDB with their details
    
    Args:
        list_docs: Whether to list document names in each collection
        show_metadata: Whether to show metadata for each document
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
            
            # Track unique file names
            unique_files = set()
            for metadata in all_docs["metadatas"]:
                file_name = metadata.get("file_name", "")
                if not file_name and "source" in metadata:
                    file_name = os.path.basename(metadata["source"])
                if file_name:
                    unique_files.add(file_name)
            
            # Print unique file names
            for file_name in sorted(unique_files):
                print(f"    - {file_name}")
                
            # Show metadata for each document if requested
            if show_metadata:
                print("  Document metadata:")
                for i, metadata in enumerate(all_docs["metadatas"]):
                    doc_id = all_docs["ids"][i] if "ids" in all_docs else f"doc_{i}"
                    print(f"    Document ID: {doc_id}")
                    for key, value in metadata.items():
                        print(f"      {key}: {value}")
                    print()  # Empty line between documents

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List ChromaDB collections")
    parser.add_argument("--list_docs", action="store_true", help="List document names in each collection")
    parser.add_argument("--show_metadata", action="store_true", help="Show metadata for each document")
    args = parser.parse_args()
    
    list_collections(args.list_docs, args.show_metadata)