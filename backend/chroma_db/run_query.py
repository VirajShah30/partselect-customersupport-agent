import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

CHROMA_DIR = "./chroma_appliance_parts"
COLLECTION_NAME = "partselect_parts"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# --- INIT ---
client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection(name=COLLECTION_NAME)
embedder = SentenceTransformer(EMBEDDING_MODEL)

# --- Rehydrate part_id_map from ChromaDB ---
def build_part_id_map(collection):
    part_id_map = {}
    all_docs = collection.get(include=["metadatas"])
    for meta in all_docs["metadatas"]:
        pid = meta["part_id"].strip().lower()
        part_id_map[pid] = meta
    return part_id_map

# --- Exact match lookup ---
def exact_match(query, part_id_map):
    for pid, meta in part_id_map.items():
        if pid in query.lower():
            return f"""Part {meta['part_id']} — {meta['title']}
        Brand: {meta['brand']}
        Description: {meta['description']}
        Symptoms: {meta['symptoms']}
        Installation: {meta['installation_difficulty']} in {meta['installation_time']}
        Video: {meta['video_url']}
        URL: {meta['url']}"""
        return None

# --- Semantic search with ChromaDB ---
def semantic_lookup(query, collection, embedder, k=3):
    query_vec = embedder.encode(query).tolist()
    results = collection.query(query_embeddings=[query_vec], n_results=k)

    output = "No exact match found. Here are some possible results:\n"
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        output += f"\n🔹 {meta['title']} (Part ID: {meta['part_id']})\n"
        output += f"Brand: {meta['brand']}, Price: {meta['price']}, Availability: {meta['availability']}\n"
        # output += f"Installation: {meta['installation_difficulty']} ({meta['installation_time']})\n"
        # output += f"Symptoms: {meta['symptoms']}\n"
        # output += f"URL: {meta['url']}\n"
    return output

# --- MAIN ---
def main():
    print("🔁 Loading part metadata from ChromaDB...")
    part_id_map = build_part_id_map(collection)

    # --- Sample Exact Match Query ---
    query_1 = "PS11701542"
    print(f"\n🧪 Test Query 1 (Exact Match): {query_1}")
    result_1 = exact_match(query_1, part_id_map)
    if result_1:
        print("\nExact Match Result:")
        print(result_1)
    else:
        print("\nNo exact match found.")

    # --- Sample Semantic Query ---
    query_2 = "My Whirlpool fridge is leaking water"
    print(f"\nTest Query 2 (Semantic Lookup): {query_2}")
    result_2 = semantic_lookup(query_2, collection, embedder)
    print("\nSemantic Lookup Result:")
    print(result_2)

if __name__ == "__main__":
    main()
