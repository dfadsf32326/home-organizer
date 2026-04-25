import json

with open("temp_scripts/repair_spaces5.json", "r", encoding="utf-8") as f:
    res = json.load(f)

data_list = res.get("data", {}).get("data", [])
for row in data_list:
    rid = None
    name = None
    for val in row:
        if isinstance(val, str):
            if val.startswith("recvh"):
                rid = val
            elif not val.startswith("space_") and "2026" not in val and len(val) > 2 and len(val) < 20:
                name = val
    if name in ["家人病历袋", "保险合同袋子"]:
        print(f"RID: {rid} -> Name: {name}")

