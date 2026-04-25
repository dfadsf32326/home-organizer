import json
import os

STAGING_FILE = "data/staging/staging_items.json"
SPACE_MAP_FILE = "data/space_map.json"

# Load space ID
with open(SPACE_MAP_FILE, "r", encoding="utf-8") as f:
    space_data = json.load(f)

# The structure is {"spaces": [...list of spaces...]}
spaces = space_data.get("spaces", [])

target_space_id = None
for space in spaces:
    name = space.get("name", "")
    if "证件" in name and "复印件" in name:
        target_space_id = space.get("id")
        print(f"Found target space: {name} (ID: {target_space_id})")
        break

if not target_space_id:
    print("WARNING: Could not find target space! Using placeholder.")
    target_space_id = "UNKNOWN_SPACE"

items = [
    {
        "name": "身份证复印件",
        "major": "文档资产",
        "minor": "证件与证明",
        "id": target_space_id,
        "quantity": 1,
        "status": "normal"
    },
    {
        "name": "身份证、户口本复印件",
        "major": "文档资产",
        "minor": "证件与证明",
        "id": target_space_id,
        "quantity": 2,
        "status": "normal"
    },
    {
        "name": "活动公司试用员工合同",
        "major": "文档资产",
        "minor": "财务与合同",
        "id": target_space_id,
        "quantity": 1,
        "status": "normal"
    },
    {
        "name": "商业保密协议",
        "major": "文档资产",
        "minor": "财务与合同",
        "id": target_space_id,
        "quantity": 1,
        "status": "normal"
    },
    {
        "name": "活动公司离职证明",
        "major": "文档资产",
        "minor": "财务与合同",
        "id": target_space_id,
        "quantity": 1,
        "status": "normal"
    },
    {
        "name": "泛微劳动合同",
        "major": "文档资产",
        "minor": "财务与合同",
        "id": target_space_id,
        "quantity": 1,
        "status": "normal"
    },
    {
        "name": "泛微终止劳动合同协议书",
        "major": "文档资产",
        "minor": "财务与合同",
        "id": target_space_id,
        "quantity": 1,
        "status": "normal"
    }
]

os.makedirs("data/staging", exist_ok=True)
with open(STAGING_FILE, "w", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=2)

print(f"Prepared {len(items)} items in staging file.")
