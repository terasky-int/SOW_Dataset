"""
Simple script to check the embedding model used in ChromaDB
"""
import chromadb

def check_embedding_model():
    """
    Check the embedding model used in ChromaDB by testing with different dimensions
    """
    # Common embedding model dimensions and their corresponding models
    dimension_to_model = {
        384: "all-MiniLM-L6-v2",
        768: ["all-mpnet-base-v2", "all-MiniLM-L12-v2"],
        512: "paraphrase-multilingual-MiniLM-L12-v2",
        1024: "paraphrase-mpnet-base-v2",
        1536: "text-embedding-ada-002 (OpenAI)"
    }
    
    print("Checking embedding model used in ChromaDB...")
    
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Get all collections
    collections = client.list_collections()
    
    if not collections:
        print("No collections found in the database.")
        return
    
    for collection in collections:
        print(f"\nCollection: {collection.name}")
        
        # Try to query with different dimensions to identify the correct one
        for dim in [1536, 768, 384, 512, 1024]:
            try:
                # Create a dummy vector of the current dimension to test
                dummy_vector = [0.0] * dim
                # Try to query with this vector
                collection.query(query_embeddings=[dummy_vector], n_results=1)
                
                print(f"✓ FOUND: This collection uses {dim}-dimensional embeddings")
                
                if dim in dimension_to_model:
                    model = dimension_to_model[dim]
                    if isinstance(model, list):
                        print(f"Possible embedding models:")
                        for m in model:
                            print(f"  - {m}")
                    else:
                        print(f"Embedding model: {model}")
                else:
                    print(f"Unknown embedding model with dimension {dim}")
                
                # No need to check other dimensions once we find the correct one
                break
                
            except Exception as e:
                # Check if error message contains dimension information
                error_msg = str(e).lower()
                if "expecting embedding with dimension of " in error_msg:
                    try:
                        # Extract the expected dimension from the error message
                        expected_dim = int(error_msg.split("expecting embedding with dimension of ")[1].split(",")[0])
                        print(f"✓ FOUND: This collection expects {expected_dim}-dimensional embeddings")
                        
                        if expected_dim in dimension_to_model:
                            model = dimension_to_model[expected_dim]
                            if isinstance(model, list):
                                print(f"Possible embedding models:")
                                for m in model:
                                    print(f"  - {m}")
                            else:
                                print(f"Embedding model: {model}")
                        else:
                            print(f"Unknown embedding model with dimension {expected_dim}")
                        
                        # No need to check other dimensions
                        break
                    except:
                        pass

if __name__ == "__main__":
    check_embedding_model()