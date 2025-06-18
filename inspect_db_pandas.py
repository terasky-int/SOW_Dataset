import pandas as pd
import argparse
import database_manager

parser = argparse.ArgumentParser(description="ChromaDB Inspection Script")
parser.add_argument("--csvout", action="store_true", help="export results to CSV")
parser.add_argument("--stdout", action="store_true", help="export results to STDOUT")
parser.add_argument("--csvpath", type=str, help="Path to the output CSV file")
args = parser.parse_args()

if __name__ == "__main__":
    db_manager = database_manager.ChromaDBManager()
    
    # Get all collections
    results = db_manager.get_collection("ts_sow_all")
    documents = results["documents"]
    metadatas = results["metadatas"]    
    rows = []

    for meta in results["metadatas"]:
        flat_meta = {k: str(v) for k, v in meta.items()}
        rows.append({**flat_meta})  # truncate long text

    df = pd.DataFrame(rows)
    if args.csvout:
        if not args.csvpath:
            raise ValueError("--csvpath is required when using --csvout mode")
        try:
            df.to_csv(args.csvpath, index=False)
            print(f"Data exported to {args.csvpath}")
            if args.stdout:
                print(df.head())
            exit()
        except Exception as e:
            print(f"Error writing to CSV: {e}")
            exit(1)
            
    print(df.head())
    
        
        
