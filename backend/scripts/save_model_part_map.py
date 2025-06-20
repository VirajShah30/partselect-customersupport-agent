import pandas as pd
import json

CSV_PATHS = [
    "data/model_parts_map_dishwasher.csv",
    "data/model_parts_map_refrigerator.csv"
]

model_to_parts = {}

for path in CSV_PATHS:
    df = pd.read_csv(path).fillna("")
    df.rename(columns=lambda x: x.strip().lower(), inplace=True)

    for _, row in df.iterrows():
        model = row["model_name"].strip().lower()
        parts = [p.strip().lower() for p in row["part_ids"].split("|") if p.strip()]

        if model not in model_to_parts:
            model_to_parts[model] = set()

        model_to_parts[model].update(parts)

# Convert sets to lists for JSON serialization
model_to_parts = {k: sorted(list(v)) for k, v in model_to_parts.items()}

# Save as JSON
with open("model_to_parts_map.json", "w") as f:
    json.dump(model_to_parts, f, indent=2, sort_keys=True)

print("✅ Saved model_to_parts_map.json")
