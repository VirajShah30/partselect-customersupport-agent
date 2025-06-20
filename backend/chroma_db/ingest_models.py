import csv
import chromadb
from chromadb.config import Settings

CHROMA_DIR = "chroma_store"
CSV_PATH = "data/model_parts_map_refrigerator.csv"
COLLECTION_NAME = "model_parts"

def load_csv(path):
    data = []
    with open(path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def main():
    # ✅ New client interface — no deprecated error
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    try:
        client.delete_collection(COLLECTION_NAME)  # Optional cleanup
    except:
        pass

    collection = client.get_or_create_collection(COLLECTION_NAME)

    records = load_csv(CSV_PATH)
    print(f"📥 Ingesting {len(records)} records into ChromaDB...")

    for idx, row in enumerate(records):
        model_name = row["model_name"]
        part_ids = row["part_ids"]

        collection.add(
            documents=[part_ids],
            metadatas=[{"model": model_name}],
            ids=[f"model-part-{idx}"]
        )

    print("✅ Ingestion complete.")

if __name__ == "__main__":
    main()
