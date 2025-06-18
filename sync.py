"""
Sync tool to generate tracking files from existing ChromaDB collections
"""
import os
import argparse
from database_manager import ChromaDBManager

def sync_tracking_file(collection_name="documents"):
    """
    Generate tracking file from existing collection data
    
    Args:
        collection_name: Name of the collection to sync
    """
    db_manager = ChromaDBManager()
    
    # Create tracking file path
    tracking_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                f"processed_files_{collection_name}.txt")
    
    try:
        # Get collection
        collection = db_manager.create_collection(collection_name)
        
        # Get all documents
        all_docs = collection.get()
        
        if not all_docs or not all_docs.get("metadatas"):
            print(f"No documents found in collection: {collection_name}")
            return
        
        # Extract unique source file paths
        source_files = set()
        for metadata in all_docs["metadatas"]:
            if "source" in metadata:
                source_files.add(metadata["source"])
        
        # Write to tracking file
        with open(tracking_file, 'w', encoding='utf-8') as f:
            for file_path in source_files:
                f.write(f"{file_path}\n")
        
        print(f"Successfully synced {len(source_files)} file paths to {tracking_file}")
        
    except Exception as e:
        print(f"Error syncing tracking file: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync tracking files from ChromaDB collections")
    parser.add_argument("--collection", default="documents", 
                        help="Collection name to sync tracking file for")
    args = parser.parse_args()
    
    sync_tracking_file(args.collection)