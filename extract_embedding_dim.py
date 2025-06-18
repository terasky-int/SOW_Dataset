import os
import sqlite3
import numpy as np
import struct

def extract_embedding_dimension():
    """
    Extract embedding dimension from ChromaDB by examining binary data files
    """
    # Common embedding model dimensions and their corresponding models
    dimension_to_model = {
        384: "all-MiniLM-L6-v2",
        768: ["all-mpnet-base-v2", "all-MiniLM-L12-v2"],
        512: "paraphrase-multilingual-MiniLM-L12-v2",
        1024: "paraphrase-mpnet-base-v2",
        1536: "text-embedding-ada-002 (OpenAI)"
    }
    
    # Path to ChromaDB
    db_path = "./chroma_db"
    
    # Method 1: Try to get dimension from SQLite database
    print("Method 1: Checking SQLite database...")
    sqlite_path = os.path.join(db_path, "chroma.sqlite3")
    if os.path.exists(sqlite_path):
        try:
            conn = sqlite3.connect(sqlite_path)
            cursor = conn.cursor()
            
            # Try to get embeddings from the database
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"Tables in database: {[t[0] for t in tables]}")
            
            if ('embeddings',) in tables:
                cursor.execute("SELECT embedding FROM embeddings LIMIT 1;")
                row = cursor.fetchone()
                if row and row[0]:
                    # Try to parse the embedding
                    try:
                        import json
                        embedding = json.loads(row[0])
                        if isinstance(embedding, list):
                            dim = len(embedding)
                            print(f"Found embedding dimension: {dim}")
                            if dim in dimension_to_model:
                                model = dimension_to_model[dim]
                                print(f"Likely model: {model}")
                            else:
                                print(f"Unknown model with dimension {dim}")
                            return
                    except:
                        print("Could not parse embedding as JSON")
            
            conn.close()
        except Exception as e:
            print(f"Error with SQLite: {str(e)}")
    
    # Method 2: Try to read binary data files
    print("\nMethod 2: Examining binary data files...")
    for root, dirs, files in os.walk(db_path):
        if "data_level0.bin" in files:
            data_file = os.path.join(root, "data_level0.bin")
            print(f"Found data file: {data_file}")
            
            try:
                # Read the binary file
                with open(data_file, 'rb') as f:
                    # Read first few bytes to determine format
                    header = f.read(16)  # Read first 16 bytes
                    
                    # Try to determine vector size from file size and number of vectors
                    file_size = os.path.getsize(data_file)
                    print(f"File size: {file_size} bytes")
                    
                    # Try different approaches to determine dimension
                    # Approach 1: Try to read as float32 array
                    try:
                        f.seek(0)
                        data = np.fromfile(f, dtype=np.float32)
                        # Guess dimensions based on common values
                        for dim in sorted(dimension_to_model.keys()):
                            if len(data) % dim == 0:
                                num_vectors = len(data) // dim
                                print(f"Possible dimension: {dim} (would give {num_vectors} vectors)")
                                if dim in dimension_to_model:
                                    model = dimension_to_model[dim]
                                    if isinstance(model, list):
                                        print(f"Possible models: {', '.join(model)}")
                                    else:
                                        print(f"Likely model: {model}")
                    except Exception as e:
                        print(f"Error reading as float32: {str(e)}")
            except Exception as e:
                print(f"Error reading data file: {str(e)}")
    
    # Method 3: Check if there's a length.bin file which might contain vector dimensions
    print("\nMethod 3: Checking length.bin file...")
    for root, dirs, files in os.walk(db_path):
        if "length.bin" in files:
            length_file = os.path.join(root, "length.bin")
            print(f"Found length file: {length_file}")
            
            try:
                with open(length_file, 'rb') as f:
                    # Try to read as 32-bit integers
                    data = np.fromfile(f, dtype=np.int32)
                    if len(data) > 0:
                        print(f"First few values: {data[:5]}")
                        # If any value matches known dimensions
                        for val in data[:5]:
                            if val in dimension_to_model:
                                print(f"Possible dimension: {val}")
                                model = dimension_to_model[val]
                                if isinstance(model, list):
                                    print(f"Possible models: {', '.join(model)}")
                                else:
                                    print(f"Likely model: {model}")
            except Exception as e:
                print(f"Error reading length file: {str(e)}")

if __name__ == "__main__":
    extract_embedding_dimension()