"""
Script to check the embedding model used in ChromaDB
"""
import os
import pickle
import chromadb
from chromadb.config import Settings

def check_embedding_model():
    """
    Check the embedding model used in ChromaDB
    """
    # Path to the ChromaDB directory
    persist_directory = "./chroma_db"
    
    # 1. Try to get model info from ChromaDB client
    print("Method 1: Checking ChromaDB client configuration...")
    try:
        client = chromadb.PersistentClient(path=persist_directory)
        
        # Get client info
        client_info = client._server._settings
        print(f"ChromaDB settings: {client_info}")
        
        # Try to access embedding function info
        embedding_function = getattr(client, "_embedding_function", None)
        if embedding_function:
            print(f"Embedding function: {embedding_function}")
    except Exception as e:
        print(f"Error checking client configuration: {str(e)}")
    
    # 2. Try to read metadata from pickle file
    print("\nMethod 2: Checking index_metadata.pickle...")
    try:
        # Find all index_metadata.pickle files
        for root, _, files in os.walk(persist_directory):
            for file in files:
                if file == "index_metadata.pickle":
                    pickle_path = os.path.join(root, file)
                    print(f"Found metadata file: {pickle_path}")
                    
                    with open(pickle_path, 'rb') as f:
                        metadata = pickle.load(f)
                        print(f"Metadata content: {metadata}")
                        
                        # Look for embedding model info
                        if isinstance(metadata, dict):
                            for key, value in metadata.items():
                                if "embedding" in str(key).lower() or "model" in str(key).lower():
                                    print(f"Potential embedding info - {key}: {value}")
    except Exception as e:
        print(f"Error reading metadata file: {str(e)}")
    
    # 3. Check collection settings
    print("\nMethod 3: Checking collection settings...")
    try:
        client = chromadb.PersistentClient(path=persist_directory)
        collections = client.list_collections()
        
        for collection in collections:
            print(f"Collection: {collection.name}")
            try:
                # Try to access collection metadata
                metadata = collection.metadata
                print(f"Collection metadata: {metadata}")
                
                # Check if embedding function info is available
                if hasattr(collection, "_embedding_function"):
                    print(f"Collection embedding function: {collection._embedding_function}")
            except Exception as e:
                print(f"Error accessing collection details: {str(e)}")
    except Exception as e:
        print(f"Error listing collections: {str(e)}")

if __name__ == "__main__":
    check_embedding_model()