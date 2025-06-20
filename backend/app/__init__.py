from flask import Flask, request, jsonify
import json
import chromadb
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import traceback
import re
import os
from dotenv import load_dotenv

# Initialize DeepSeek client
load_dotenv()
deepseek_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
)

app = Flask(__name__)

# Load part_id_map
with open("part_id_map.json", "r") as f:
    part_id_map = json.load(f)

# Load model_to_parts_map
with open("model_to_parts_map.json", "r") as f:
    model_to_parts_map = json.load(f)

# Init ChromaDB and embedder
CHROMA_DIR = "./chroma_appliance_parts"
COLLECTION_NAME = "partselect_parts"
client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection(name=COLLECTION_NAME)

def is_part_compatible_with_model(model_id: str, part_id: str) -> bool:
    model_id = model_id.strip().lower()
    part_id = part_id.strip().lower()
    return model_id in model_to_parts_map and part_id in model_to_parts_map[model_id]

def compatibility_check(part_id: str, model_id: str):
    compatible = is_part_compatible_with_model(model_id, part_id)
    return f"✅ Yes, part {part_id} is compatible with model {model_id}." if compatible else f"❌ No, part {part_id} is not compatible with model {model_id}."

def exact_match(part_id: str):
    meta = part_id_map.get(part_id.lower())
    if meta:
        return f"""Part {meta['part_id']} — {meta['title']}
                Brand: {meta['brand']}
                Description: {meta['description']}
                Symptoms: {meta['symptoms']}
                Installation: {meta['installation_difficulty']} in {meta['installation_time']}
                Video: {meta['video_url']}
                URL: {meta['url']}"""
    return "⚠️ Part not found."

def semantic_lookup(query: str, k=5):
    results = collection.query(query_texts=[query], n_results=k)
    parsed = []
    for entry in results["documents"][0]:
        part = {}

        def extract(key, multiline=False):
            pattern = rf"{key}:\s*(.*?)(?:\n|$)"
            match = re.search(pattern, entry, re.DOTALL if multiline else 0)
            return match.group(1).strip() if match else ""

        part["title"] = extract("Title")
        part["description"] = extract("Description", multiline=True)
        part["symptoms"] = [s.strip() for s in extract("Symptoms").split("|") if s.strip()]
        part["product_types"] = [pt.strip().replace(".", "") for pt in extract("Product Types").split(",") if pt.strip()]
        part["part_id"] = extract("Part ID")
        part["brand"] = extract("Brand")
        part["installation"] = extract("Installation")
        part["related_parts"] = [p.strip() for p in extract("Related Parts").split(",") if p.strip()]
        part["replacement_parts"] = [p.strip() for p in extract("Replacement Parts").split(",") if p.strip()]
        part["url"] = extract("URL")

        parsed.append(part)
    return parsed

def clean_and_parse_json(raw):
    try:
        cleaned = re.sub(r"^```json|```$", "", raw.strip(), flags=re.MULTILINE).strip()
        return json.loads(cleaned)
    except Exception as e:
        raise ValueError(f"Failed to parse DeepSeek JSON output: {e}")

def generate_final_response(user_query: str, classification: dict, context: any):
    try:
        system_prompt = (
            "You are a helpful, expert customer service agent for appliance parts — "
            "specifically refrigerators and dishwashers. Your role is to assist users with "
            "part installation, compatibility, or troubleshooting using only the context provided. "
            "Avoid guessing. If context is missing, politely say so — but if installation time or difficulty are missing, you may suggest a typical time range like 'usually under 30 minutes' and assume it's easy if not specified.\n\n"
            "Answer must:\n"
            "- Be clear, specific, and confident\n"
            "- Stick to appliance part knowledge\n"
            "- Include relevant installation difficulty and estimated time if possible\n"
            "- Return the part's URL if available or else say 'not available'\n"
            "- Return youtube video from context if available or else say 'not available'\n"
        )   

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""Query: {user_query}

Classification: {json.dumps(classification, indent=2)}

Context Retrieved:
{json.dumps(context, indent=2) if isinstance(context, (dict, list)) else str(context)}

Generate a user-facing response based on this context and classification."""}
        ]

        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=False
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"❌ Error generating final response: {str(e)}"

@app.route("/ask", methods=["POST"])
def ask():
    query = request.json.get("query", "")
    try:
        classification_prompt = f"""
You are a helpful and knowledgeable appliance repair assistant who specializes in refrigerator and dishwasher parts.

Your job is to analyze user queries and classify them into one of three categories:
1. "exact" — when the user asks specifically about how to install a part or get info about a part number.
2. "compatibility" — when the user asks if a specific part is compatible with their appliance model.
3. "semantic" — if it's a general symptom-based or brand/product inquiry.

Strictly return a JSON with:
"type": one of ["exact", "compatibility", "semantic", "out_of_scope"],
"part_id": if mentioned (e.g., PS11752778),
"model_id": if mentioned (e.g., WDT780SAEM1),
"brand": if any (e.g., Whirlpool),
"symptoms": if any (e.g., ice not working, leaking water),
"product_types": if any (e.g., refrigerator, dishwasher)

Only answer about refrigerator and dishwasher part questions. If the query is about something else, mark it as "out_of_scope".
Now process this query: {query}
"""

        completion = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful, focused assistant. Only answer about appliance parts."},
                {"role": "user", "content": classification_prompt}
            ],
            stream=False
        )

        raw_content = completion.choices[0].message.content
        result = clean_and_parse_json(raw_content)

        query_type = result.get("type")
        context_data = ""

        if query_type == "out_of_scope":
            context_data = {"response": "Sorry, I can only assist with refrigerator and dishwasher part queries."}

        elif query_type == "exact" and result.get("part_id"):
            context_data = exact_match(result["part_id"])

        elif query_type == "compatibility" and result.get("part_id") and result.get("model_id"):
            context_data = compatibility_check(result["part_id"], result["model_id"])

        elif query_type == "semantic":
            context_str = result.get("brand", "") + " " + str(result.get("product_types", "")) + " " + str(result.get("symptoms", ""))
            context_data = semantic_lookup(context_str)

        else:
            context_data = {"error": "Hmm, I couldn't confidently understand that query. Can you rephrase it?"}

        final_response = generate_final_response(query, result, context_data)
        return jsonify({"response": final_response})

    except Exception as e:
        return jsonify({
            "error": "Internal error during query classification",
            "details": str(e),
            "trace": traceback.format_exc()
        })

if __name__ == "__main__":
    app.run(port=5001, debug=True)
