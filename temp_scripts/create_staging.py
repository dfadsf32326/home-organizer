import json
import os
import uuid
from datetime import datetime

STAGING_FILE = os.path.expanduser("~/.hermes/skills/custom/home-organizer/data/staging/staging_items.json")

# 确保目录存在
os.makedirs(os.path.dirname(STAGING_FILE), exist_ok=True)

# 物品清单
items_to_add = [
    {"name": "NeutroCost 肌醇 454g", "sub_category": "营养补剂", "remark": ""},
    {"name": "nutricost 碳酸氢钾 Potassium Bicarbonate 907g", "sub_category": "营养补剂", "remark": ""},
    {"name": "氯化钾 500g", "sub_category": "营养补剂", "remark": ""},
    {"name": "食品干燥剂", "sub_category": "厨房消耗品", "remark": "防潮保鲜用"},
    {"name": "维生素C钠 1kg", "sub_category": "营养补剂", "remark": "2024-07-08生产，有效期24个月（至2026-07）"},
    {"name": "明胶 100g", "sub_category": "粮油/调味品", "remark": ""},
    {"name": "胶原蛋白肽 150g", "sub_category": "营养补剂", "remark": "未开封"},
    {"name": "维C 200g", "sub_category": "营养补剂", "remark": ""},
    {"name": "天然活化斜发沸石粉", "sub_category": "营养补剂", "remark": ""},
    {"name": "甜菜碱盐酸盐 200g", "sub_category": "营养补剂", "remark": ""},
    {"name": "麦角硫因 5g", "sub_category": "营养补剂", "remark": ""},
    {"name": "喜马拉雅海盐", "sub_category": "粮油/调味品", "remark": ""},
    {"name": "菠萝蛋白酶", "sub_category": "营养补剂", "remark": ""},
    {"name": "脂肪酶", "sub_category": "营养补剂", "remark": ""},
    {"name": "牛磺酸 200g", "sub_category": "营养补剂", "remark": ""},
    {"name": "乳糖 100g", "sub_category": "粮油/调味品", "remark": ""},
    {"name": "谷氨酰胺", "sub_category": "营养补剂", "remark": "已开封"},
    {"name": "葵花卵磷脂 200g", "sub_category": "营养补剂", "remark": "共3包（200g/包）"},
    {"name": "葵花卵磷脂 200g", "sub_category": "营养补剂", "remark": "共3包（200g/包）"},
    {"name": "葵花卵磷脂 200g", "sub_category": "营养补剂", "remark": "共3包（200g/包）"},
    {"name": "鲁戈氏碘液 (5%浓度 50ml)", "sub_category": "营养补剂", "remark": ""}
]

with open(os.path.expanduser("~/.hermes/skills/custom/home-organizer/data/category_mapping.json"), "r", encoding="utf-8") as f:
    category_mapping = json.load(f)

staging_data = []
now_str = datetime.now().isoformat()

for item in items_to_add:
    cat_info = category_mapping.get(item["sub_category"])
    
    new_item = {
        "id": f"item-{uuid.uuid4().hex[:8]}",
        "name": item["name"],
        "category": cat_info["major"],
        "sub_category": item["sub_category"],
        "category_record_id": cat_info["record_id"],
        "space_record_id": "recvic1jZFkHEI",
        "location": "暂存区",
        "container": "补剂散装原料箱",
        "remark": item["remark"],
        "status": ["盘点中"],
        "feishu_record_id": "",
        "created_at": now_str,
        "updated_at": now_str
    }
    staging_data.append(new_item)

with open(STAGING_FILE, "w", encoding="utf-8") as f:
    json.dump(staging_data, f, ensure_ascii=False, indent=2)

print(f"Staging file created successfully with {len(staging_data)} items.")
