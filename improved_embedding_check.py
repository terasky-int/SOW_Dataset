import chromadb
import pickle
import os
import glob

def analyze_embeddings():
    # Common embedding model dimensions and their corresponding models
    dimension_to_model = {
        384: "all-MiniLM-L6-v2",
        768: ["all-mpnet-base-v2", "all-MiniLM-L12-v2"],
        512: "paraphrase-multilingual-MiniLM-L12-v2",
        1024: "paraphrase-mpnet-base-v2",
        1536: "text-embedding-ada-002 (OpenAI)"
    }

    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Get all collections
    collections = client.list_collections()
    
    if not collections:
        print("No collections found in the database.")
        return

    print("\nAnalyzing ChromaDB collections:")
    for collection in collections:
        print(f"\nCollection: {collection.name}")
        
        # Get collection items
        try:
            items = collection.get(limit=1)
            if items and 'embeddings' in items and items['embeddings'] and len(items['embeddings']) > 0:
                embedding_dim = len(items['embeddings'][0])
                print(f"Embedding dimension: {embedding_dim}")
                
                # Match dimension to possible models
                if embedding_dim in dimension_to_model:
                    models = dimension_to_model[embedding_dim]
                    if isinstance(models, list):
                        print("Possible embedding models:")
                        for model in models:
                            print(f"- {model}")
                    else:
                        print(f"Likely embedding model: {models}")
                else:
                    print(f"Unknown embedding model for dimension {embedding_dim}")
            else:
                print("No embeddings found in collection or collection is empty")
        except Exception as e:
            print(f"Error getting collection items: {str(e)}")

def direct_file_inspection():
    # Common embedding model dimensions and their corresponding models
    dimension_to_model = {
        384: "all-MiniLM-L6-v2",
        768: ["all-mpnet-base-v2", "all-MiniLM-L12-v2"],
        512: "paraphrase-multilingual-MiniLM-L12-v2",
        1024: "paraphrase-mpnet-base-v2",
        1536: "text-embedding-ada-002 (OpenAI)"
    }
    
    print("\nDirect inspection of database files:")
    
    # Look for UUID-like directories in chroma_db
    uuid_dirs = []
    for item in os.listdir("./chroma_db"):
        item_path = os.path.join("./chroma_db", item)
        if os.path.isdir(item_path) and len(item) > 30:  # Simple heuristic for UUID dirs
            uuid_dirs.append(item_path)
    
    if not uuid_dirs:
        print("No UUID-like directories found in chroma_db")
        return
        
    for dir_path in uuid_dirs:
        print(f"\nExamining directory: {dir_path}")
        metadata_path = os.path.join(dir_path, "index_metadata.pickle")
        
        if os.path.exists(metadata_path):
            print(f"Found metadata file: {metadata_path}")
            try:
                with open(metadata_path, 'rb') as f:
                    metadata = pickle.load(f)
                
                if isinstance(metadata, dict):
                    print("Metadata keys:", list(metadata.keys()))
                    
                    if 'dimensionality' in metadata:
                        dim = metadata['dimensionality']
                        print(f"Dimensionality: {dim}")
                        
                        if dim in dimension_to_model:
                            models = dimension_to_model[dim]
                            if isinstance(models, list):
                                print("Possible embedding models:")
                                for model in models:
                                    print(f"- {model}")
                            else:
                                print(f"Likely embedding model: {models}")
                        else:
                            print(f"Unknown model with dimension {dim}")
            except Exception as e:
                print(f"Error reading metadata file: {str(e)}")

if __name__ == "__main__":
    try:
        analyze_embeddings()
    except Exception as e:
        print(f"Error in analyze_embeddings: {str(e)}")
    
    # Always run direct file inspection as a backup
    direct_file_inspection()