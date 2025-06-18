"""
Main module for the document scraping AI agent
"""
import os
import argparse
from typing import List, Dict, Any
from pdf_scraper import PDFScraper
from document_scraper import DocumentScraper
from database_manager import ChromaDBManager
from ai_agent import AIAgent, AgentState

def process_file(file_path: str, collection_name: str = "documents") -> None:
    """
    Process a file and store it in the database
    
    Args:
        file_path: Path to the file
        collection_name: Name of the collection to store the data
    """
    # Initialize components
    doc_scraper = DocumentScraper()
    db_manager = ChromaDBManager()
    
    print(f"Processing file: {file_path}")
    
    # Extract text and metadata from file
    try:
        text = doc_scraper.extract_text(file_path)
        metadata = doc_scraper.extract_metadata(file_path)
        
        # Add file_name to metadata if not present
        if "file_name" not in metadata:
            metadata["file_name"] = os.path.basename(file_path)
            
        print(f"Extracted {len(text)} characters from file")
        print(f"Metadata: {metadata}")
        
        # Chunk the text
        chunks = doc_scraper.chunk_text(text)
        print(f"Split into {len(chunks)} chunks")
        
        # Prepare metadata for each chunk
        metadatas = []
        for i, _ in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_id"] = i
            chunk_metadata["source"] = file_path
            metadatas.append(chunk_metadata)
        
        # Store in database
        db_manager.add_documents(
            collection_name=collection_name,
            documents=chunks,
            metadatas=metadatas
        )
        
        print(f"Successfully stored in collection: {collection_name}")
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")

def process_folder(folder_path: str, collection_name: str = "documents", recursive: bool = False, 
                name_filter: str = None, force_reprocess: bool = False) -> None:
    """
    Process all supported files in a folder and store them in the database
    
    Args:
        folder_path: Path to the folder
        collection_name: Name of the collection to store the data
        recursive: Whether to search recursively in subfolders
        name_filter: Only process files containing this string in their filename
        force_reprocess: Whether to force reprocessing of already processed files
    """
    if not os.path.isdir(folder_path):
        print(f"Error: {folder_path} is not a valid directory")
        return
    
    supported_extensions = [
        '.pdf', '.txt', '.docx', '.doc', 
        '.xlsx', '.xls', '.pptx', '.ppt',
        '.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'
    ]
    
    # Create a tracking file for processed files
    tracking_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"processed_files_{collection_name}.txt")
    processed_files_set = set()
    
    # Load previously processed files if tracking file exists
    if os.path.exists(tracking_file) and not force_reprocess:
        try:
            with open(tracking_file, 'r', encoding='utf-8') as f:
                processed_files_set = set(line.strip() for line in f if line.strip())
            print(f"Found {len(processed_files_set)} previously processed files")
        except Exception as e:
            print(f"Error reading tracking file: {str(e)}")
    
    processed_count = 0
    skipped_count = 0
    
    print(f"Processing folder: {folder_path}")
    
    if recursive:
        walk_iter = os.walk(folder_path)
    else:
        # Only process the top directory when not recursive
        walk_iter = [(folder_path, [], [f for f in os.listdir(folder_path) 
                     if os.path.isfile(os.path.join(folder_path, f))])]
    
    # Open tracking file for appending new processed files
    with open(tracking_file, 'a', encoding='utf-8') as tracking:
        for root, _, files in walk_iter:
            for file in files:
                # Apply name filter if specified (case-insensitive)
                if name_filter and name_filter.lower() not in file.lower():
                    continue
                
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file_path)[1].lower()
                
                if file_ext in supported_extensions:
                    # Skip if already processed and not forcing reprocess
                    if file_path in processed_files_set and not force_reprocess:
                        print(f"Skipping already processed file: {file_path}")
                        skipped_count += 1
                        continue
                    
                    try:
                        process_file(file_path, collection_name)
                        # Add to tracking file
                        tracking.write(f"{file_path}\n")
                        tracking.flush()  # Ensure it's written immediately
                        processed_count += 1
                    except Exception as e:
                        print(f"Error processing {file_path}: {str(e)}")
    
    print(f"Processed {processed_count} files, skipped {skipped_count} files from folder: {folder_path}")

def query_database(query: str, collection_name: str = "documents") -> None:
    """
    Query the database and process results with AI
    
    Args:
        query: Query text
        collection_name: Name of the collection to query
    """
    # Initialize components
    db_manager = ChromaDBManager()
    ai_agent = AIAgent()
    
    print(f"Querying database with: {query}")
    
    try:
        # Query the database
        results = db_manager.query_collection(
            collection_name=collection_name,
            query_text=query,
            n_results=4000
        )
        
        if not results or not results.get("documents"):
            print("No results found")
            return
        
        # Process with AI agent
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        
        # Get source file names for display
        source_files = []
        for metadata in metadatas:
            if "file_name" in metadata:
                source_files.append(metadata["file_name"])
            elif "source" in metadata:
                source_files.append(os.path.basename(metadata["source"]))
        
        source_files = list(set(source_files))  # Remove duplicates
        
        print(f"Found {len(documents)} relevant chunks from {len(source_files)} files:")
        for file in source_files:
            print(f"- {file}")
        
        # Create agent graph
        agent_graph = ai_agent.create_agent_graph()
        
        # Run the agent
        result = agent_graph.invoke({
            "input": query,
            "context": documents,
            "question": "",
            "answer": "",
            "metadata": {"source_metadatas": metadatas}
        })
        
        print("\nAI Response:")
        print(result["answer"])
        
    except Exception as e:
        print(f"Error querying database: {str(e)}")

def update_collection_metadata(collection_name: str, root_path: str) -> None:
    """
    Update metadata for all documents in a collection based on folder structure
    
    Args:
        collection_name: Name of the ChromaDB collection
        root_path: Root path of the documents
    """
    import re
    
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
        
        # Skip if file is not under the root path
        if not source_path.startswith(root_path):
            continue
        
        # Get relative path from root
        rel_path = os.path.relpath(source_path, root_path)
        path_parts = rel_path.split(os.sep)
        
        # Initialize folder metadata
        folder_metadata = {}
        
        # Extract client name (first folder after root)
        if len(path_parts) > 0:
            folder_metadata["client_name"] = path_parts[0]
        
        # Look for year folder (folder that contains only a 4-digit number)
        for j, part in enumerate(path_parts):
            if re.match(r'^\d{4}
                # Project title is likely the folder after the year
                if j + 1 < len(path_parts) and os.path.isdir(os.path.join(root_path, *path_parts[:j+2])):
                    folder_metadata["project_title"] = path_parts[j+1]
                break
        
        # If no year folder found but we have at least 2 levels, assume second level is project title
        if "year" not in folder_metadata and len(path_parts) > 1:
            folder_metadata["project_title"] = path_parts[1]
        
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

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Document Scraping AI Agent")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Process file command
    process_file_parser = subparsers.add_parser("process-file", help="Process a single file")
    process_file_parser.add_argument("file_path", help="Path to the file")
    process_file_parser.add_argument("--collection", default="documents", help="Collection name")
    
    # Process folder command
    process_folder_parser = subparsers.add_parser("process-folder", help="Process all files in a folder")
    process_folder_parser.add_argument("folder_path", help="Path to the folder")
    process_folder_parser.add_argument("--collection", default="documents", help="Collection name")
    process_folder_parser.add_argument("--recursive", "-r", action="store_true", help="Search recursively in subfolders")
    process_folder_parser.add_argument("--filter", "-f", help="Only process files containing this string in their filename")
    process_folder_parser.add_argument("--force", action="store_true", help="Force reprocessing of already processed files")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query the database")
    query_parser.add_argument("query", help="Query text")
    query_parser.add_argument("--collection", default="documents", help="Collection name")
    
    # Update metadata command
    update_metadata_parser = subparsers.add_parser("update-metadata", help="Update metadata based on folder structure")
    update_metadata_parser.add_argument("--collection", required=True, help="Collection name")
    update_metadata_parser.add_argument("--root_path", required=True, 
                        help="Root path of the documents (e.g., 'G:\\.shortcut-targets-by-id\\0B73ZDFS_-IuiMXE2ZGh3aW9KWms\\Sales\\Customers\\')")
    
    args = parser.parse_args()
    
    if args.command == "process-file":
        process_file(args.file_path, args.collection)
    elif args.command == "process-folder":
        process_folder(args.folder_path, args.collection, args.recursive, args.filter, args.force)
    elif args.command == "query":
        query_database(args.query, args.collection)
    elif args.command == "update-metadata":
        update_collection_metadata(args.collection, args.root_path)
    else:
        parser.print_help()

if __name__ == "__main__":
    main(), part):
                folder_metadata["year"] = part
                # Project title is likely the folder after the year
                if j + 1 < len(path_parts) and os.path.isdir(os.path.join(root_path, *path_parts[:j+2])):
                    folder_metadata["project_title"] = path_parts[j+1]
                break
        
        # If no year folder found but we have at least 2 levels, assume second level is project title
        if "year" not in folder_metadata and len(path_parts) > 1:
            folder_metadata["project_title"] = path_parts[1]
        
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

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Document Scraping AI Agent")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Process file command
    process_file_parser = subparsers.add_parser("process-file", help="Process a single file")
    process_file_parser.add_argument("file_path", help="Path to the file")
    process_file_parser.add_argument("--collection", default="documents", help="Collection name")
    
    # Process folder command
    process_folder_parser = subparsers.add_parser("process-folder", help="Process all files in a folder")
    process_folder_parser.add_argument("folder_path", help="Path to the folder")
    process_folder_parser.add_argument("--collection", default="documents", help="Collection name")
    process_folder_parser.add_argument("--recursive", "-r", action="store_true", help="Search recursively in subfolders")
    process_folder_parser.add_argument("--filter", "-f", help="Only process files containing this string in their filename")
    process_folder_parser.add_argument("--force", action="store_true", help="Force reprocessing of already processed files")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query the database")
    query_parser.add_argument("query", help="Query text")
    query_parser.add_argument("--collection", default="documents", help="Collection name")
    
    # Update metadata command
    update_metadata_parser = subparsers.add_parser("update-metadata", help="Update metadata based on folder structure")
    update_metadata_parser.add_argument("--collection", required=True, help="Collection name")
    update_metadata_parser.add_argument("--root_path", required=True, 
                        help="Root path of the documents (e.g., 'G:\\.shortcut-targets-by-id\\0B73ZDFS_-IuiMXE2ZGh3aW9KWms\\Sales\\Customers\\')")
    
    args = parser.parse_args()
    
    if args.command == "process-file":
        process_file(args.file_path, args.collection)
    elif args.command == "process-folder":
        process_folder(args.folder_path, args.collection, args.recursive, args.filter, args.force)
    elif args.command == "query":
        query_database(args.query, args.collection)
    elif args.command == "update-metadata":
        update_collection_metadata(args.collection, args.root_path)
    else:
        parser.print_help()

if __name__ == "__main__":
    main(), part):
                folder_metadata["year"] = part
                # Project title is likely the folder after the year
                if j + 1 < len(path_parts) and os.path.isdir(os.path.join(root_path, *path_parts[:j+2])):
                    folder_metadata["project_title"] = path_parts[j+1]
                break
        
        # If no year folder found but we have at least 2 levels, assume second level is project title
        if "year" not in folder_metadata and len(path_parts) > 1:
            folder_metadata["project_title"] = path_parts[1]
        
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

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Document Scraping AI Agent")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Process file command
    process_file_parser = subparsers.add_parser("process-file", help="Process a single file")
    process_file_parser.add_argument("file_path", help="Path to the file")
    process_file_parser.add_argument("--collection", default="documents", help="Collection name")
    
    # Process folder command
    process_folder_parser = subparsers.add_parser("process-folder", help="Process all files in a folder")
    process_folder_parser.add_argument("folder_path", help="Path to the folder")
    process_folder_parser.add_argument("--collection", default="documents", help="Collection name")
    process_folder_parser.add_argument("--recursive", "-r", action="store_true", help="Search recursively in subfolders")
    process_folder_parser.add_argument("--filter", "-f", help="Only process files containing this string in their filename")
    process_folder_parser.add_argument("--force", action="store_true", help="Force reprocessing of already processed files")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query the database")
    query_parser.add_argument("query", help="Query text")
    query_parser.add_argument("--collection", default="documents", help="Collection name")
    
    # Update metadata command
    update_metadata_parser = subparsers.add_parser("update-metadata", help="Update metadata based on folder structure")
    update_metadata_parser.add_argument("--collection", required=True, help="Collection name")
    update_metadata_parser.add_argument("--root_path", required=True, 
                        help="Root path of the documents (e.g., 'G:\\.shortcut-targets-by-id\\0B73ZDFS_-IuiMXE2ZGh3aW9KWms\\Sales\\Customers\\')")
    
    args = parser.parse_args()
    
    if args.command == "process-file":
        process_file(args.file_path, args.collection)
    elif args.command == "process-folder":
        process_folder(args.folder_path, args.collection, args.recursive, args.filter, args.force)
    elif args.command == "query":
        query_database(args.query, args.collection)
    elif args.command == "update-metadata":
        update_collection_metadata(args.collection, args.root_path)
    else:
        parser.print_help()

if __name__ == "__main__":
    main(), part):
                folder_metadata["year"] = part
                # Project title is likely the folder after the year
                if j + 1 < len(path_parts) and os.path.isdir(os.path.join(root_path, *path_parts[:j+2])):
                    folder_metadata["project_title"] = path_parts[j+1]
                break
        
        # If no year folder found but we have at least 2 levels, assume second level is project title
        if "year" not in folder_metadata and len(path_parts) > 1:
            folder_metadata["project_title"] = path_parts[1]
        
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

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Document Scraping AI Agent")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Process file command
    process_file_parser = subparsers.add_parser("process-file", help="Process a single file")
    process_file_parser.add_argument("file_path", help="Path to the file")
    process_file_parser.add_argument("--collection", default="documents", help="Collection name")
    
    # Process folder command
    process_folder_parser = subparsers.add_parser("process-folder", help="Process all files in a folder")
    process_folder_parser.add_argument("folder_path", help="Path to the folder")
    process_folder_parser.add_argument("--collection", default="documents", help="Collection name")
    process_folder_parser.add_argument("--recursive", "-r", action="store_true", help="Search recursively in subfolders")
    process_folder_parser.add_argument("--filter", "-f", help="Only process files containing this string in their filename")
    process_folder_parser.add_argument("--force", action="store_true", help="Force reprocessing of already processed files")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query the database")
    query_parser.add_argument("query", help="Query text")
    query_parser.add_argument("--collection", default="documents", help="Collection name")
    
    # Update metadata command
    update_metadata_parser = subparsers.add_parser("update-metadata", help="Update metadata based on folder structure")
    update_metadata_parser.add_argument("--collection", required=True, help="Collection name")
    update_metadata_parser.add_argument("--root_path", required=True, 
                        help="Root path of the documents (e.g., 'G:\\.shortcut-targets-by-id\\0B73ZDFS_-IuiMXE2ZGh3aW9KWms\\Sales\\Customers\\')")
    
    args = parser.parse_args()
    
    if args.command == "process-file":
        process_file(args.file_path, args.collection)
    elif args.command == "process-folder":
        process_folder(args.folder_path, args.collection, args.recursive, args.filter, args.force)
    elif args.command == "query":
        query_database(args.query, args.collection)
    elif args.command == "update-metadata":
        update_collection_metadata(args.collection, args.root_path)
    else:
        parser.print_help()

if __name__ == "__main__":
    main(), part):
                # Project title is likely the folder after the year
                if j + 1 < len(path_parts) and os.path.isdir(os.path.join(root_path, *path_parts[:j+2])):
                    folder_metadata["project_title"] = path_parts[j+1]
                break
        
        # If no year folder found but we have at least 2 levels, assume second level is project title
        if "year" not in folder_metadata and len(path_parts) > 1:
            folder_metadata["project_title"] = path_parts[1]
        
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

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Document Scraping AI Agent")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Process file command
    process_file_parser = subparsers.add_parser("process-file", help="Process a single file")
    process_file_parser.add_argument("file_path", help="Path to the file")
    process_file_parser.add_argument("--collection", default="documents", help="Collection name")
    
    # Process folder command
    process_folder_parser = subparsers.add_parser("process-folder", help="Process all files in a folder")
    process_folder_parser.add_argument("folder_path", help="Path to the folder")
    process_folder_parser.add_argument("--collection", default="documents", help="Collection name")
    process_folder_parser.add_argument("--recursive", "-r", action="store_true", help="Search recursively in subfolders")
    process_folder_parser.add_argument("--filter", "-f", help="Only process files containing this string in their filename")
    process_folder_parser.add_argument("--force", action="store_true", help="Force reprocessing of already processed files")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query the database")
    query_parser.add_argument("query", help="Query text")
    query_parser.add_argument("--collection", default="documents", help="Collection name")
    
    # Update metadata command
    update_metadata_parser = subparsers.add_parser("update-metadata", help="Update metadata based on folder structure")
    update_metadata_parser.add_argument("--collection", required=True, help="Collection name")
    update_metadata_parser.add_argument("--root_path", required=True, 
                        help="Root path of the documents (e.g., 'G:\\.shortcut-targets-by-id\\0B73ZDFS_-IuiMXE2ZGh3aW9KWms\\Sales\\Customers\\')")
    
    args = parser.parse_args()
    
    if args.command == "process-file":
        process_file(args.file_path, args.collection)
    elif args.command == "process-folder":
        process_folder(args.folder_path, args.collection, args.recursive, args.filter, args.force)
    elif args.command == "query":
        query_database(args.query, args.collection)
    elif args.command == "update-metadata":
        update_collection_metadata(args.collection, args.root_path)
    else:
        parser.print_help()

if __name__ == "__main__":
    main(), part):
                folder_metadata["year"] = part
                # Project title is likely the folder after the year
                if j + 1 < len(path_parts) and os.path.isdir(os.path.join(root_path, *path_parts[:j+2])):
                    folder_metadata["project_title"] = path_parts[j+1]
                break
        
        # If no year folder found but we have at least 2 levels, assume second level is project title
        if "year" not in folder_metadata and len(path_parts) > 1:
            folder_metadata["project_title"] = path_parts[1]
        
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

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Document Scraping AI Agent")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Process file command
    process_file_parser = subparsers.add_parser("process-file", help="Process a single file")
    process_file_parser.add_argument("file_path", help="Path to the file")
    process_file_parser.add_argument("--collection", default="documents", help="Collection name")
    
    # Process folder command
    process_folder_parser = subparsers.add_parser("process-folder", help="Process all files in a folder")
    process_folder_parser.add_argument("folder_path", help="Path to the folder")
    process_folder_parser.add_argument("--collection", default="documents", help="Collection name")
    process_folder_parser.add_argument("--recursive", "-r", action="store_true", help="Search recursively in subfolders")
    process_folder_parser.add_argument("--filter", "-f", help="Only process files containing this string in their filename")
    process_folder_parser.add_argument("--force", action="store_true", help="Force reprocessing of already processed files")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query the database")
    query_parser.add_argument("query", help="Query text")
    query_parser.add_argument("--collection", default="documents", help="Collection name")
    
    # Update metadata command
    update_metadata_parser = subparsers.add_parser("update-metadata", help="Update metadata based on folder structure")
    update_metadata_parser.add_argument("--collection", required=True, help="Collection name")
    update_metadata_parser.add_argument("--root_path", required=True, 
                        help="Root path of the documents (e.g., 'G:\\.shortcut-targets-by-id\\0B73ZDFS_-IuiMXE2ZGh3aW9KWms\\Sales\\Customers\\')")
    
    args = parser.parse_args()
    
    if args.command == "process-file":
        process_file(args.file_path, args.collection)
    elif args.command == "process-folder":
        process_folder(args.folder_path, args.collection, args.recursive, args.filter, args.force)
    elif args.command == "query":
        query_database(args.query, args.collection)
    elif args.command == "update-metadata":
        update_collection_metadata(args.collection, args.root_path)
    else:
        parser.print_help()

if __name__ == "__main__":
    main(), part):
                folder_metadata["year"] = part
                # Project title is likely the folder after the year
                if j + 1 < len(path_parts) and os.path.isdir(os.path.join(root_path, *path_parts[:j+2])):
                    folder_metadata["project_title"] = path_parts[j+1]
                break
        
        # If no year folder found but we have at least 2 levels, assume second level is project title
        if "year" not in folder_metadata and len(path_parts) > 1:
            folder_metadata["project_title"] = path_parts[1]
        
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

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Document Scraping AI Agent")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Process file command
    process_file_parser = subparsers.add_parser("process-file", help="Process a single file")
    process_file_parser.add_argument("file_path", help="Path to the file")
    process_file_parser.add_argument("--collection", default="documents", help="Collection name")
    
    # Process folder command
    process_folder_parser = subparsers.add_parser("process-folder", help="Process all files in a folder")
    process_folder_parser.add_argument("folder_path", help="Path to the folder")
    process_folder_parser.add_argument("--collection", default="documents", help="Collection name")
    process_folder_parser.add_argument("--recursive", "-r", action="store_true", help="Search recursively in subfolders")
    process_folder_parser.add_argument("--filter", "-f", help="Only process files containing this string in their filename")
    process_folder_parser.add_argument("--force", action="store_true", help="Force reprocessing of already processed files")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query the database")
    query_parser.add_argument("query", help="Query text")
    query_parser.add_argument("--collection", default="documents", help="Collection name")
    
    # Update metadata command
    update_metadata_parser = subparsers.add_parser("update-metadata", help="Update metadata based on folder structure")
    update_metadata_parser.add_argument("--collection", required=True, help="Collection name")
    update_metadata_parser.add_argument("--root_path", required=True, 
                        help="Root path of the documents (e.g., 'G:\\.shortcut-targets-by-id\\0B73ZDFS_-IuiMXE2ZGh3aW9KWms\\Sales\\Customers\\')")
    
    args = parser.parse_args()
    
    if args.command == "process-file":
        process_file(args.file_path, args.collection)
    elif args.command == "process-folder":
        process_folder(args.folder_path, args.collection, args.recursive, args.filter, args.force)
    elif args.command == "query":
        query_database(args.query, args.collection)
    elif args.command == "update-metadata":
        update_collection_metadata(args.collection, args.root_path)
    else:
        parser.print_help()

if __name__ == "__main__":
    main(), part):
                folder_metadata["year"] = part
                # Project title is likely the folder after the year
                if j + 1 < len(path_parts) and os.path.isdir(os.path.join(root_path, *path_parts[:j+2])):
                    folder_metadata["project_title"] = path_parts[j+1]
                break
        
        # If no year folder found but we have at least 2 levels, assume second level is project title
        if "year" not in folder_metadata and len(path_parts) > 1:
            folder_metadata["project_title"] = path_parts[1]
        
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

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Document Scraping AI Agent")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Process file command
    process_file_parser = subparsers.add_parser("process-file", help="Process a single file")
    process_file_parser.add_argument("file_path", help="Path to the file")
    process_file_parser.add_argument("--collection", default="documents", help="Collection name")
    
    # Process folder command
    process_folder_parser = subparsers.add_parser("process-folder", help="Process all files in a folder")
    process_folder_parser.add_argument("folder_path", help="Path to the folder")
    process_folder_parser.add_argument("--collection", default="documents", help="Collection name")
    process_folder_parser.add_argument("--recursive", "-r", action="store_true", help="Search recursively in subfolders")
    process_folder_parser.add_argument("--filter", "-f", help="Only process files containing this string in their filename")
    process_folder_parser.add_argument("--force", action="store_true", help="Force reprocessing of already processed files")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query the database")
    query_parser.add_argument("query", help="Query text")
    query_parser.add_argument("--collection", default="documents", help="Collection name")
    
    # Update metadata command
    update_metadata_parser = subparsers.add_parser("update-metadata", help="Update metadata based on folder structure")
    update_metadata_parser.add_argument("--collection", required=True, help="Collection name")
    update_metadata_parser.add_argument("--root_path", required=True, 
                        help="Root path of the documents (e.g., 'G:\\.shortcut-targets-by-id\\0B73ZDFS_-IuiMXE2ZGh3aW9KWms\\Sales\\Customers\\')")
    
    args = parser.parse_args()
    
    if args.command == "process-file":
        process_file(args.file_path, args.collection)
    elif args.command == "process-folder":
        process_folder(args.folder_path, args.collection, args.recursive, args.filter, args.force)
    elif args.command == "query":
        query_database(args.query, args.collection)
    elif args.command == "update-metadata":
        update_collection_metadata(args.collection, args.root_path)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()