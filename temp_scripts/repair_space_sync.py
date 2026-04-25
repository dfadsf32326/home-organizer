import json

with open("data/space_mapping.json", "r", encoding="utf-8") as f:
    mapping = json.load(f)
print("Mapping fields:")
print(json.dumps(mapping, indent=2, ensure_ascii=False))
