import os
import json
from database_manager import ChromaDBManager
from ai_agent import AIAgent

def categorize_documents(collection_name="documents"):
    """
    Categorize documents in the database and organize them into collections
    Also extract products, client names, and document creators
    """
    # Initialize components
    db_manager = ChromaDBManager()
    ai_agent = AIAgent()
    
    # Get all documents from the main collection
    collection = db_manager.create_collection(collection_name)
    
    # Get all documents (this is a simplified approach - you might need pagination for large collections)
    all_docs = collection.get()
    
    # Define your categories
    categories = ["SOW", "POC", "Legal", "Finance", "Purchase", "Orders", "Other"]
    
    # Create collections for each category if they don't exist
    for category in categories:
        db_manager.create_collection(f"{collection_name}_{category.lower()}")
    
    # Process each document to determine its category and extract entities
    for i, doc in enumerate(all_docs["documents"]):
        doc_id = all_docs["ids"][i]
        metadata = all_docs["metadatas"][i]
        
        # Extract category, products, clients, and creator
        extraction_prompt = f"""
        Analyze this document excerpt and provide the following information in JSON format:
        1. category: Classify into one of these categories: {', '.join(categories)}
        2. products: List of product names mentioned in the document (empty list if none)
        3. clients: List of client names mentioned in the document (empty list if none)
        4. creator: Name of document creator if mentioned (empty string if not found)
        
        Return ONLY valid JSON like this:
        {{
            "category": "category_name",
            "products": ["product1", "product2"],
            "clients": ["client1", "client2"],
            "creator": "creator_name"
        }}
        """
        
        extraction_result = ai_agent.process_text(doc, extraction_prompt)
        
        try:
            # Extract JSON from the response
            json_start = extraction_result.find('{')
            json_end = extraction_result.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = extraction_result[json_start:json_end]
                extracted_data = json.loads(json_str)
                
                category = extracted_data.get("category", "Other")
                
                # Update metadata with extracted information
                metadata["products"] = extracted_data.get("products", [])
                metadata["clients"] = extracted_data.get("clients", [])
                
                # Only add creator if not already in metadata and found in document
                if "creator" not in metadata and extracted_data.get("creator"):
                    metadata["creator"] = extracted_data.get("creator")
                
                # Validate the category
                if category in categories:
                    # Add to the appropriate category collection
                    target_collection = db_manager.create_collection(f"{collection_name}_{category.lower()}")
                    target_collection.add(
                        documents=[doc],
                        metadatas=[metadata],
                        ids=[doc_id]
                    )
                    print(f"Document {doc_id} categorized as {category}")
                    print(f"  Products: {', '.join(metadata['products']) if metadata['products'] else 'None'}")
                    print(f"  Clients: {', '.join(metadata['clients']) if metadata['clients'] else 'None'}")
                    print(f"  Creator: {metadata.get('creator', 'Unknown')}")
                else:
                    print(f"Could not categorize document {doc_id}, invalid category: {category}")
            else:
                print(f"Could not extract JSON from AI response for document {doc_id}")
        except json.JSONDecodeError:
            print(f"Invalid JSON in AI response for document {doc_id}")
        except Exception as e:
            print(f"Error processing document {doc_id}: {str(e)}")

def create_product_collections(collection_name="documents"):
    """
    Create collections for each product mentioned in documents
    """
    db_manager = ChromaDBManager()
    
    # Get all documents from the main collection
    collection = db_manager.create_collection(collection_name)
    all_docs = collection.get()
    
    # Track all products
    all_products = set()
    
    # Find all products mentioned in documents
    for metadata in all_docs["metadatas"]:
        if "products" in metadata and metadata["products"]:
            for product in metadata["products"]:
                all_products.add(product)
    
    # Create collections for each product
    for product in all_products:
        product_collection_name = f"{collection_name}_product_{product.lower().replace(' ', '_')}"
        db_manager.create_collection(product_collection_name)
        
        # Find documents mentioning this product
        for i, metadata in enumerate(all_docs["metadatas"]):
            if "products" in metadata and product in metadata["products"]:
                doc_id = all_docs["ids"][i]
                doc = all_docs["documents"][i]
                
                # Add to product collection
                product_collection = db_manager.create_collection(product_collection_name)
                product_collection.add(
                    documents=[doc],
                    metadatas=[metadata],
                    ids=[doc_id]
                )
        
        print(f"Created collection for product: {product}")

def create_client_collections(collection_name="documents"):
    """
    Create collections for each client mentioned in documents
    """
    db_manager = ChromaDBManager()
    
    # Get all documents from the main collection
    collection = db_manager.create_collection(collection_name)
    all_docs = collection.get()
    
    # Track all clients
    all_clients = set()
    
    # Find all clients mentioned in documents
    for metadata in all_docs["metadatas"]:
        if "clients" in metadata and metadata["clients"]:
            for client in metadata["clients"]:
                all_clients.add(client)
    
    # Create collections for each client
    for client in all_clients:
        client_collection_name = f"{collection_name}_client_{client.lower().replace(' ', '_')}"
        db_manager.create_collection(client_collection_name)
        
        # Find documents mentioning this client
        for i, metadata in enumerate(all_docs["metadatas"]):
            if "clients" in metadata and client in metadata["clients"]:
                doc_id = all_docs["ids"][i]
                doc = all_docs["documents"][i]
                
                # Add to client collection
                client_collection = db_manager.create_collection(client_collection_name)
                client_collection.add(
                    documents=[doc],
                    metadatas=[metadata],
                    ids=[doc_id]
                )
        
        print(f"Created collection for client: {client}")

if __name__ == "__main__":
    categorize_documents("ts_harel")
    create_product_collections("ts_harel")
    create_client_collections("ts_harel")