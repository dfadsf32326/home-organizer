import json

with open("data/space_mapping.json", "r", encoding="utf-8") as f:
    mapping = json.load(f)
    for name, r in mapping.items():
        if r.get("record_id") in ["recvhN14HPrYMU", "recvhMXUk94xEj"]:
            print(f"Space: {name} -> RID: {r.get('record_id')}")

with open("data/space_map.json", "r", encoding="utf-8") as f:
    mapping = json.load(f)
    for name, r in mapping.items():
        if r.get("record_id") in ["recvhN14HPrYMU", "recvhMXUk94xEj"]:
            print(f"Space_map: {name} -> RID: {r.get('record_id')}")
