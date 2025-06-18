"""
Improved script to check the embedding model used in ChromaDB
"""
import pickle
import os
import sqlite3
import json

def check_embedding_model():
    """
    Check the embedding model used in ChromaDB by examining both pickle files and SQLite database
    """
    # Path to the ChromaDB directory
    persist_directory = "./chroma_db"
    
    # Method 1: Try to read metadata from pickle file
    print("Method 1: Checking index_metadata.pickle...")
    try:
        # Find all index_metadata.pickle files
        for root, _, files in os.walk(persist_directory):
            for file in files:
                if file == "index_metadata.pickle":
                    pickle_path = os.path.join(root, file)
                    print(f"Found metadata file: {pickle_path}")
                    
                    with open(pickle_path, 'rb') as f:
                        metadata = pickle.load(f)
                        print(f"Metadata content type: {type(metadata)}")
                        
                        # Print all keys if it's a dictionary
                        if isinstance(metadata, dict):
                            print(f"Keys: {list(metadata.keys())}")
                            
                            # Deep inspection of metadata
                            print("\nDeep inspection of metadata:")
                            for key, value in metadata.items():
                                print(f"Key: {key}, Type: {type(value)}")
                                if isinstance(value, dict) and len(value) < 10:
                                    print(f"  Subkeys: {list(value.keys())}")
                                elif isinstance(value, list) and len(value) > 0:
                                    print(f"  List length: {len(value)}, First item type: {type(value[0])}")
                            
                            # Look for embedding dimension
                            dim = None
                            if "dimensionality" in metadata:
                                dim = metadata["dimensionality"]
                            elif "dimension" in metadata:
                                dim = metadata["dimension"]
                            
                            print(f"Embedding dimension from metadata: {dim}")
    except Exception as e:
        print(f"Error reading metadata file: {str(e)}")
    
    # Method 2: Check the SQLite database
    print("\nMethod 2: Checking SQLite database...")
    try:
        db_path = os.path.join(persist_directory, "chroma.sqlite3")
        if os.path.exists(db_path):
            print(f"Found SQLite database: {db_path}")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"Tables in database: {[table[0] for table in tables]}")
            
            # Check embeddings table
            try:
                cursor.execute("SELECT * FROM embeddings LIMIT 1;")
                embedding_row = cursor.fetchone()
                if embedding_row:
                    print("Found embedding data in database")
                    # Get column names
                    column_names = [description[0] for description in cursor.description]
                    print(f"Embedding table columns: {column_names}")
                    
                    # Try to find embedding data
                    embedding_idx = None
                    for i, col in enumerate(column_names):
                        if col == 'embedding':
                            embedding_idx = i
                            break
                    
                    if embedding_idx is not None and embedding_row[embedding_idx]:
                        # Try to parse the embedding data
                        try:
                            embedding_data = json.loads(embedding_row[embedding_idx])
                            if isinstance(embedding_data, list):
                                print(f"Found embedding dimension: {len(embedding_data)}")
                                
                                # Map dimension to possible models
                                model_map = {
                                    384: "all-MiniLM-L6-v2 (most likely)",
                                    768: "all-mpnet-base-v2 or all-MiniLM-L12-v2",
                                    512: "paraphrase-multilingual-MiniLM-L12-v2",
                                    1024: "paraphrase-mpnet-base-v2",
                                    1536: "text-embedding-ada-002 (OpenAI)"
                                }
                                
                                dim = len(embedding_data)
                                if dim in model_map:
                                    print(f"Likely model: {model_map[dim]}")
                                else:
                                    print(f"Unknown model with dimension {dim}")
                        except:
                            print("Could not parse embedding data as JSON")
            except sqlite3.OperationalError as e:
                print(f"Error querying embeddings table: {str(e)}")
            
            # Check collections table for metadata
            try:
                cursor.execute("SELECT name, metadata FROM collections;")
                collections = cursor.fetchall()
                print(f"\nFound {len(collections)} collections")
                
                for i, (name, metadata) in enumerate(collections):
                    print(f"Collection {i+1}: {name}")
                    if metadata:
                        try:
                            metadata_dict = json.loads(metadata)
                            print(f"  Metadata: {metadata_dict}")
                            
                            # Look for embedding function info
                            if 'hnsw:space' in metadata_dict:
                                print(f"  Distance metric: {metadata_dict['hnsw:space']}")
                            
                            if 'embedding_function' in metadata_dict:
                                print(f"  Embedding function: {metadata_dict['embedding_function']}")
                        except:
                            print("  Could not parse metadata as JSON")
            except sqlite3.OperationalError as e:
                print(f"Error querying collections table: {str(e)}")
            
            conn.close()
    except Exception as e:
        print(f"Error examining SQLite database: {str(e)}")

if __name__ == "__main__":
    check_embedding_model()