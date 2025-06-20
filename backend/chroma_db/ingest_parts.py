import os
import chromadb
from chromadb.config import Settings
from uuid import uuid4
import pandas as pd
from sentence_transformers import SentenceTransformer

CHROMA_DIR = "./chroma_appliance_parts"

# --- CONFIG ---  # Replace with your actual CSV file paths
COLLECTION_NAME = "partselect_parts"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Swap with DeepSeek embedding if needed

# --- INIT ---
client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection(name=COLLECTION_NAME)
embedder = SentenceTransformer(EMBEDDING_MODEL)

# --- LOAD + INGEST ---
def ingest_csv_to_chroma(file_path, start_idx=0):
    df = pd.read_csv(file_path).fillna("")

    for i, row in df.iterrows():
        idx = start_idx + i
        part_id = f"part_{idx}"

        content = f"""
        Title: {row['title']}
        Description: {row['description']}
        Symptoms: {row['symptoms']}
        Product Types: {row['product_types']}
        Part ID: {row['part_id']}
        Brand: {row['brand']}
        Installation: {row['installation_difficulty']} in {row['installation_time']}
        Related Parts: {row['related_parts']}
        Replacement Parts: {row['replacement_parts']}
        URL: {row['video_url']}
        """

        embedding = embedder.encode(content).tolist()
        metadata = {
            "product_types": row["product_types"],
            "symptoms": row["symptoms"],
            "brand": row["brand"],
            "part_id": row['part_id']
        }

        collection.add(
            ids=[part_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata]
        )

def main():
    # Initialize Chroma client
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(name="partselect_parts")

    # Ingest CSVs
    #ingest_csv_to_chroma("data/appliance_parts_dishwasher.csv")
    #ingest_csv_to_chroma("data/appliance_parts_refrigerator.csv")

    # print("✅ Ingestion complete.")

    # Test query
    query = "Whirlpool fridge ice maker not working"
    results = collection.query(
        query_texts=[query],
        n_results=5
    )

    print("\n🔍 Sample Query Results:")
    for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
        print(doc)
        print("----------------")


if __name__ == "__main__":
    main()
