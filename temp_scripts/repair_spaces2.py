import json

with open("data/space_map.json", "r", encoding="utf-8") as f:
    mapping = json.load(f)
    for name, r in mapping.items():
        if r in ["recvhN14HPrYMU", "recvhMXUk94xEj"]:
            print(f"Space_map: {name} -> RID: {r}")

with open("data/space_mapping.json", "r", encoding="utf-8") as f:
    mapping = json.load(f)
    for name, r in mapping.items():
        if r in ["recvhN14HPrYMU", "recvhMXUk94xEj"]:
            print(f"Space_mapping: {name} -> RID: {r}")
