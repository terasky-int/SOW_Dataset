"""
Script to check the embedding dimensions in ChromaDB
"""
import sqlite3
import numpy as np
import os

def check_embedding_dimensions():
    """
    Check the embedding dimensions in ChromaDB SQLite database
    """
    # Path to the ChromaDB SQLite file
    db_path = "./chroma_db/chroma.sqlite3"
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if embeddings table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='embeddings'")
        if not cursor.fetchone():
            print("No 'embeddings' table found in the database")
            
            # List all tables to find where embeddings might be stored
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Available tables: {[t[0] for t in tables]}")
            
            # Try to find embedding data in other tables
            for table in [t[0] for t in tables]:
                try:
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    col_names = [col[1] for col in columns]
                    
                    # Check if any column might contain embedding data
                    embedding_cols = [col for col in col_names if "embedding" in col.lower()]
                    if embedding_cols:
                        print(f"Table '{table}' has potential embedding columns: {embedding_cols}")
                        
                        # Try to get a sample
                        for col in embedding_cols:
                            cursor.execute(f"SELECT {col} FROM {table} LIMIT 1")
                            sample = cursor.fetchone()
                            if sample and sample[0]:
                                try:
                                    # Try to parse as bytes
                                    embedding_bytes = sample[0]
                                    if isinstance(embedding_bytes, bytes):
                                        embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                                        print(f"Found embedding with dimension: {len(embedding)}")
                                        print(f"This suggests the model is using {len(embedding)}-dimensional embeddings")
                                        print_possible_models(len(embedding))
                                except Exception as e:
                                    print(f"Could not parse embedding data: {str(e)}")
                except Exception as e:
                    print(f"Error inspecting table {table}: {str(e)}")
            return
        
        # Get a sample embedding to determine dimensions
        cursor.execute("SELECT embedding FROM embeddings LIMIT 1")
        sample = cursor.fetchone()
        
        if sample and sample[0]:
            try:
                # Parse the embedding bytes
                embedding_bytes = sample[0]
                embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                
                print(f"Found embedding with dimension: {len(embedding)}")
                print(f"This suggests the model is using {len(embedding)}-dimensional embeddings")
                
                # Print possible models based on dimensions
                print_possible_models(len(embedding))
                
            except Exception as e:
                print(f"Error parsing embedding data: {str(e)}")
        else:
            print("No embedding data found in the database")
        
        conn.close()
        
    except Exception as e:
        print(f"Error accessing database: {str(e)}")

def print_possible_models(dimension):
    """
    Print possible sentence-transformer models based on embedding dimension
    """
    model_dimensions = {
        384: ["all-MiniLM-L6-v2", "all-MiniLM-L6-v1"],
        768: ["all-mpnet-base-v2", "all-distilroberta-v1", "all-MiniLM-L12-v2"],
        512: ["paraphrase-multilingual-MiniLM-L12-v2"],
        1024: ["paraphrase-mpnet-base-v2"]
    }
    
    if dimension in model_dimensions:
        print(f"Possible sentence-transformers models with {dimension} dimensions:")
        for model in model_dimensions[dimension]:
            print(f"- {model}")
    else:
        print(f"No common sentence-transformers models with {dimension} dimensions found in reference list")

if __name__ == "__main__":
    check_embedding_dimensions()