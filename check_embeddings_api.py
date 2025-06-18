import chromadb
import json
import sqlite3
import os

def check_embeddings_api():
    """
    Check embeddings using ChromaDB API and direct database access
    """
    # Common embedding model dimensions and their corresponding models
    dimension_to_model = {
        384: "all-MiniLM-L6-v2",
        768: ["all-mpnet-base-v2", "all-MiniLM-L12-v2"],
        512: "paraphrase-multilingual-MiniLM-L12-v2",
        1024: "paraphrase-mpnet-base-v2",
        1536: "text-embedding-ada-002 (OpenAI)"
    }
    
    print("Method 1: Using ChromaDB API")
    try:
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path="./chroma_db")
        
        # Get all collections
        collections = client.list_collections()
        print(f"Found {len(collections)} collections")
        
        for collection in collections:
            print(f"\nCollection: {collection.name}")
            
            # Try to get collection info
            try:
                # Try to peek at collection data
                print("Trying to get collection data...")
                
                # Try with include parameter
                try:
                    items = collection.get(include=["embeddings"], limit=1)
                    if items and 'embeddings' in items and items['embeddings'] and len(items['embeddings']) > 0:
                        embedding_dim = len(items['embeddings'][0])
                        print(f"Embedding dimension: {embedding_dim}")
                        
                        if embedding_dim in dimension_to_model:
                            model = dimension_to_model[embedding_dim]
                            if isinstance(model, list):
                                print(f"Possible models: {', '.join(model)}")
                            else:
                                print(f"Likely model: {model}")
                        else:
                            print(f"Unknown model with dimension {embedding_dim}")
                        return
                except Exception as e:
                    print(f"Error with include parameter: {str(e)}")
                
                # Try with different API
                try:
                    print("Trying alternative API...")
                    # Try to query with a dummy vector to see dimension
                    for dim in [1536, 768, 384, 512, 1024]:
                        try:
                            print(f"Testing with dimension {dim}...")
                            dummy_vector = [0.0] * dim
                            results = collection.query(query_embeddings=[dummy_vector], n_results=1)
                            print(f"Query with dimension {dim} succeeded!")
                            print(f"Likely embedding dimension: {dim}")
                            
                            if dim in dimension_to_model:
                                model = dimension_to_model[dim]
                                if isinstance(model, list):
                                    print(f"Possible models: {', '.join(model)}")
                                else:
                                    print(f"Likely model: {model}")
                            return
                        except Exception as e:
                            if "dimension mismatch" in str(e).lower():
                                print(f"Dimension {dim} is not correct")
                            else:
                                print(f"Error with dimension {dim}: {str(e)}")
                except Exception as e:
                    print(f"Error with alternative API: {str(e)}")
            except Exception as e:
                print(f"Error getting collection info: {str(e)}")
    except Exception as e:
        print(f"Error with ChromaDB API: {str(e)}")
    
    print("\nMethod 2: Direct SQLite access")
    try:
        # Connect to SQLite database
        db_path = os.path.join("./chroma_db", "chroma.sqlite3")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Try to get embedding data
            try:
                cursor.execute("SELECT * FROM embeddings LIMIT 1;")
                columns = [description[0] for description in cursor.description]
                print(f"Columns in embeddings table: {columns}")
                
                # Look for embedding column
                embedding_col = None
                for col in columns:
                    if "embedding" in col.lower():
                        embedding_col = col
                        break
                
                if embedding_col:
                    cursor.execute(f"SELECT {embedding_col} FROM embeddings LIMIT 1;")
                    row = cursor.fetchone()
                    if row and row[0]:
                        try:
                            # Try to parse as JSON
                            embedding = json.loads(row[0])
                            if isinstance(embedding, list):
                                dim = len(embedding)
                                print(f"Found embedding dimension: {dim}")
                                
                                if dim in dimension_to_model:
                                    model = dimension_to_model[dim]
                                    if isinstance(model, list):
                                        print(f"Possible models: {', '.join(model)}")
                                    else:
                                        print(f"Likely model: {model}")
                                else:
                                    print(f"Unknown model with dimension {dim}")
                        except:
                            print("Could not parse embedding data as JSON")
            except Exception as e:
                print(f"Error querying embeddings: {str(e)}")
            
            conn.close()
    except Exception as e:
        print(f"Error with SQLite: {str(e)}")

if __name__ == "__main__":
    check_embeddings_api()