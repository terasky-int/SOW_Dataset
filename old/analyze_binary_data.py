import os
import numpy as np
import struct

def analyze_binary_data():
    """
    Analyze binary data file to determine embedding dimension
    """
    # Common embedding model dimensions and their corresponding models
    dimension_to_model = {
        384: "all-MiniLM-L6-v2",
        768: ["all-mpnet-base-v2", "all-MiniLM-L12-v2"],
        512: "paraphrase-multilingual-MiniLM-L12-v2",
        1024: "paraphrase-mpnet-base-v2",
        1536: "text-embedding-ada-002 (OpenAI)"
    }
    
    # Path to data file
    data_file = "./chroma_db/4be78c66-a018-4913-b6d3-4d2d65d05534/data_level0.bin"
    
    if not os.path.exists(data_file):
        print(f"Data file not found: {data_file}")
        return
    
    # Get file size
    file_size = os.path.getsize(data_file)
    print(f"Data file size: {file_size} bytes")
    
    # Assuming data is stored as float32 (4 bytes per value)
    total_floats = file_size // 4
    print(f"Total float32 values: {total_floats}")
    
    # Try to determine number of vectors and dimension
    print("\nPossible dimensions based on common embedding sizes:")
    
    # Check if file size is divisible by common dimensions
    for dim in sorted(dimension_to_model.keys()):
        if total_floats % dim == 0:
            num_vectors = total_floats // dim
            print(f"Dimension {dim}: Would give {num_vectors} vectors")
            
            # Check if this is a likely model
            if dim in dimension_to_model:
                model = dimension_to_model[dim]
                if isinstance(model, list):
                    print(f"  Possible models: {', '.join(model)}")
                else:
                    print(f"  Likely model: {model}")
    
    # Try to read the first vector to confirm
    print("\nAttempting to read first vector...")
    try:
        with open(data_file, 'rb') as f:
            # Read first 100 float32 values
            data = np.fromfile(f, dtype=np.float32, count=100)
            print(f"First few values: {data[:10]}")
            
            # Check if values look like embeddings (typically between -1 and 1)
            if np.all(np.abs(data) < 10):
                print("Values look like embeddings (within reasonable range)")
            else:
                print("Values don't look like typical embeddings")
                
            # Try to detect pattern in data
            print("\nAnalyzing data pattern...")
            
            # Read more data to analyze
            f.seek(0)
            sample_size = min(1000000, file_size // 4)  # Read up to 1M floats or file size
            data = np.fromfile(f, dtype=np.float32, count=sample_size)
            
            # Look for repeating patterns that might indicate vector boundaries
            for dim in [768, 1536, 384, 512, 1024]:  # Check common dimensions
                if len(data) >= dim * 2:
                    # Check correlation between consecutive potential vectors
                    correlation = np.corrcoef(data[:dim], data[dim:2*dim])[0, 1]
                    print(f"Correlation between consecutive {dim}-dim vectors: {correlation:.4f}")
    
    except Exception as e:
        print(f"Error analyzing data: {str(e)}")

if __name__ == "__main__":
    analyze_binary_data()