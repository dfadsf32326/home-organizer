import json

with open("temp_scripts/repair_spaces5.json", "r", encoding="utf-8") as f:
    res = json.load(f)

data_list = res.get("data", {}).get("data", [])
for row in data_list:
    rid = None
    name = None
    for val in row:
        if isinstance(val, str):
            if val.startswith("recv"):
                rid = val
            elif not val.startswith("space_") and len(val) > 2 and "2026-" not in val:
                # heuristic for name
                name = val
    if rid in ["recvhN14HPrYMU", "recvhMXUk94xEj"]:
        # Find the exact name which is likely the first string element
        exact_name = [v for v in row if isinstance(v, str) and not v.startswith("recv") and not v.startswith("space_") and "2026" not in v][0]
        print(f"RID: {rid} -> Name: {exact_name}")

