import json

with open("data/space_tree.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for node in data.get("nodes", []):
    name = node.get("name", "")
    if "说明" in name or "书" in name:
        print(f"Name: {name}, ID: {node.get('id')}, Record_ID: {node.get('record_id')}")

