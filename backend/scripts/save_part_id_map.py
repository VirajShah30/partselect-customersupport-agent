import pandas as pd
import json

CSV_PATHS = [
    "data/appliance_parts_dishwasher.csv",
    "data/appliance_parts_refrigerator.csv"
]

part_id_map = {}

for path in CSV_PATHS:
    df = pd.read_csv(path).fillna("")
    for _, row in df.iterrows():
        pid = row["part_id"].strip().lower()
        part_id_map[pid] = {
            "part_id": row["part_id"],
            "brand": row["brand"],
            "title": row["title"],
            "description": row["description"],
            "symptoms": row["symptoms"],
            "product_types": row["product_types"],
            "installation_difficulty": row["installation_difficulty"],
            "installation_time": row["installation_time"],
            "video_url": row["video_url"],
            "url": row["url"],
            "price": row["price"],
            "availability": row["availability"]
        }

with open("part_id_map.json", "w") as f:
    json.dump(part_id_map, f)

print(" Saved part_id_map.json")
