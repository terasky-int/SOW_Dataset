"""
Script to update metadata in ChromaDB documents based on folder structure
with embedded root path to avoid command line parsing issues
"""
import os
import re
from typing import Dict, List, Any, Optional
from database_manager import ChromaDBManager

def extract_folder_metadata(file_path: str, root_path: str) -> Dict[str, str]:
    """
    Extract metadata from folder structure
    
    Args:
        file_path: Full path to the document
        root_path: Root path of the documents
        
    Returns:
        Dictionary with extracted metadata
    """
    # Initialize metadata
    metadata = {
        "client_name": None,
        "year": None,
        "project_title": None,
        "source": file_path
    }
    
    # Skip if file is not under the root path
    if not file_path.startswith(root_path):
        return metadata
    
    # Get relative path from root
    rel_path = os.path.relpath(file_path, root_path)
    path_parts = rel_path.split(os.sep)
    
    # Extract client name (first folder after root)
    if len(path_parts) > 0:
        metadata["client_name"] = path_parts[0]
    
    # Look for year folder (folder that contains only a 4-digit number)
    for i, part in enumerate(path_parts):
        if re.match(r'^\d{4}$', part):
            metadata["year"] = part
            # Project title is likely the folder after the year
            if i + 1 < len(path_parts) and os.path.isdir(os.path.join(root_path, *path_parts[:i+2])):
                metadata["project_title"] = path_parts[i+1]
            break
    
    # If no year folder found but we have at least 2 levels, assume second level is project title
    if metadata["year"] is None and len(path_parts) > 1:
        metadata["project_title"] = path_parts[1]
    
    return metadata

def update_collection_metadata(collection_name: str, root_path: str) -> None:
    """
    Update metadata for all documents in a collection based on folder structure
    
    Args:
        collection_name: Name of the ChromaDB collection
        root_path: Root path of the documents
    """
    db_manager = ChromaDBManager()
    collection = db_manager.create_collection(collection_name)
    
    # Get all documents in the collection
    all_docs = collection.get()
    
    if not all_docs or "metadatas" not in all_docs or len(all_docs["metadatas"]) == 0:
        print(f"No documents found in collection {collection_name}")
        return
    
    print(f"Updating metadata for {len(all_docs['metadatas'])} documents in {collection_name}")
    
    # Track documents that need updating
    updated_docs = []
    updated_metadatas = []
    updated_ids = []
    
    # Process each document
    for i, metadata in enumerate(all_docs["metadatas"]):
        doc_id = all_docs["ids"][i]
        document = all_docs["documents"][i]
        
        # Skip if no source field
        if "source" not in metadata:
            print(f"Skipping document {doc_id} - no source field")
            continue
        
        source_path = metadata["source"]
        
        # Extract folder metadata
        folder_metadata = extract_folder_metadata(source_path, root_path)
        
        # Check if we need to update metadata
        needs_update = False
        for key, value in folder_metadata.items():
            if value is not None and (key not in metadata or metadata[key] != value):
                needs_update = True
                break
        
        if needs_update:
            # Create updated metadata
            new_metadata = metadata.copy()
            for key, value in folder_metadata.items():
                if value is not None:
                    new_metadata[key] = value
            
            updated_docs.append(document)
            updated_metadatas.append(new_metadata)
            updated_ids.append(doc_id)
    
    # Update documents in batches
    batch_size = 100
    for i in range(0, len(updated_docs), batch_size):
        batch_docs = updated_docs[i:i+batch_size]
        batch_metadatas = updated_metadatas[i:i+batch_size]
        batch_ids = updated_ids[i:i+batch_size]
        
        print(f"Updating batch {i//batch_size + 1}/{(len(updated_docs) + batch_size - 1)//batch_size}")
        
        # Update documents with new metadata
        collection.update(
            ids=batch_ids,
            metadatas=batch_metadatas
        )
    
    print(f"Updated metadata for {len(updated_docs)} documents")

if __name__ == "__main__":
    # Embedded configuration - no need for command line arguments
    COLLECTION_NAME = "ts_sow_all"
    ROOT_PATH = r"G:\.shortcut-targets-by-id\0B73ZDFS_-IuiMXE2ZGh3aW9KWms\Sales\Customers"
    
    print(f"Starting metadata update for collection: {COLLECTION_NAME}")
    print(f"Using root path: {ROOT_PATH}")
    
    update_collection_metadata(COLLECTION_NAME, ROOT_PATH)