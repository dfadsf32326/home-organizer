import json
import os

target_space_id = "space_a3mZBT"
data = {
    "items": [
        {
            "name": "一张身份证复印件",
            "major": "文档资产",
            "minor": "证件与证明",
            "id": target_space_id,
            "quantity": 1,
            "status": ["正常"]
        }
    ]
}

os.makedirs("data/staging", exist_ok=True)
with open("data/staging/staging_items.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("==== Staging file content preview ====")
print(json.dumps(data, ensure_ascii=False, indent=2))
