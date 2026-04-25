import json
import subprocess
import os

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
TABLE_ID = "tbluMVXBpHIJDGyi"

with open("temp_scripts/repair_items6.json", "r", encoding="utf-8") as f:
    res = json.load(f)

# Update local items to set the correct space via record update
items = res.get("data", {}).get("data", [])
record_ids = res.get("data", {}).get("record_id_list", [])

update_list = []
for idx, item in enumerate(items):
    name = None
    for val in item:
        if isinstance(val, str) and len(val) > 1 and "2026" not in val and not val.startswith("item"):
            name = val
            break
            
    if name is None:
        continue
        
    space_id = None
    if "病历" in name or "体检" in name or "报告" in name or "化验" in name or "眼科" in name:
        space_id = "recvhN14HPrYMU" # 我的病历相关文件袋
    elif "合同" in name or "保单" in name or "车险" in name or "保险" in name:
        space_id = "recvhMXUk94xEj" # 工作与合同文件袋
        
    if space_id is not None:
        rid = record_ids[idx]
        print(f"To Update: {name} -> Space RID: {space_id} (Item RID: {rid})")
        update_list.append({
            "record_id": rid,
            "fields": {
                "fld2AIT7oG": [
                    {"id": space_id}
                ]
            }
        })

print(f"Total to update: {len(update_list)}")

for up in update_list:
    cmd = [LARK_CLI, "base", "+record-upsert", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--record-id", up["record_id"], "--json", json.dumps(up["fields"], ensure_ascii=False)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if "ok\":true" not in r.stdout.replace(" ", ""):
        print(f"Update failed for {up['record_id']}: {r.stderr}")
    else:
        print(f"Updated {up['record_id']}")

