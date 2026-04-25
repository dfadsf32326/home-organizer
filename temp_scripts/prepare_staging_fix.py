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
            "name": "活动公司的离职证明",
            "major": "文档资产",
            "minor": "财务与合同",
            "id": target_space_id,
            "quantity": 1,
            "status": "normal"
        },
        {
            "name": "泛微的劳动合同",
            "major": "文档资产",
            "minor": "财务与合同",
            "id": target_space_id,
            "quantity": 1,
            "status": "normal"
        },
        {
            "name": "泛微的终止劳动合同协议书",
            "major": "文档资产",
            "minor": "财务与合同",
            "id": target_space_id,
            "quantity": 1,
            "status": "normal"
        }
    ]
}

os.makedirs("data/staging", exist_ok=True)
with open("data/staging/staging_items.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Staging data written successfully.")
