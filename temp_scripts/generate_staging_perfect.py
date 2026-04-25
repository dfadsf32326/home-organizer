import json
import os

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Load data
space_data = load_json("data/space_tree.json")
category_map = load_json("data/category_mapping.json")

# 1. 查找空间ID (space_tree.json has a "nodes" array based on your latest file check)
if isinstance(space_data, dict) and "nodes" in space_data:
    spaces = space_data["nodes"]
elif isinstance(space_data, list):
    spaces = space_data
else:
    spaces = []

space_name = "证件及复印件袋子"
space_record_id = None
space_local_id = None

for s in spaces:
    if isinstance(s, dict) and s.get("name") == space_name:
        space_record_id = s.get("record_id")
        space_local_id = s.get("id")
        break

def get_cat_info(sub_name):
    if sub_name in category_map:
        return category_map[sub_name].get("major"), category_map[sub_name].get("record_id")
    return None, None

# 2. 准备原始盘点数据
raw_items = [
    {"name": "一张身份证复印件", "sub_category": "证件与证明", "quantity": 1},
    {"name": "两张身份证、户口本复印件", "sub_category": "证件与证明", "quantity": 2},
    {"name": "活动公司的试用员工合同", "sub_category": "财务与合同", "quantity": 1},
    {"name": "商业保密协议", "sub_category": "财务与合同", "quantity": 1},
    {"name": "活动公司的离职证明", "sub_category": "财务与合同", "quantity": 1},
    {"name": "泛微的劳动合同", "sub_category": "财务与合同", "quantity": 1},
    {"name": "泛微的终止劳动合同协议书", "sub_category": "财务与合同", "quantity": 1}
]

# 3. 组装完美的Staging结构
staging_items = []
for item in raw_items:
    major, cat_record_id = get_cat_info(item["sub_category"])
    
    st_item = {
        "name": item["name"],
        "category": major,
        "sub_category": item["sub_category"],
        "category_record_id": cat_record_id,
        "space_record_id": space_record_id,
        "location": "暂存区",
        "container": space_name,
        "id": space_local_id,
        "quantity": item["quantity"],
        "status": ["正常"]
    }
    staging_items.append(st_item)

output_data = {"items": staging_items}

os.makedirs("data/staging", exist_ok=True)
with open("data/staging/staging_items.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print("==== 完整生成的本地 Staging 结构 (前两项) ====")
print(json.dumps(output_data["items"][:2], ensure_ascii=False, indent=2))
print(f"==== 共生成了 {len(staging_items)} 条记录 ====")

