import json
import os

# 读取空间获取 record_id
try:
    with open("data/space_tree.json", "r", encoding="utf-8") as f:
        spaces = json.load(f).get("nodes", [])
    space_id = next((s["record_id"] for s in spaces if s.get("name") == "说明书文件袋"), None)
except Exception as e:
    space_id = None
    print(f"Error reading space_tree.json: {e}")

# 读取分类获取 record_id
try:
    with open("data/category_mapping.json", "r", encoding="utf-8") as f:
        cats = json.load(f)
    cat_id = cats.get("说明书与保修卡", {}).get("record_id")
except Exception as e:
    cat_id = None
    print(f"Error reading category_mapping.json: {e}")

items_list = [
    "米家微波炉使用说明书",
    "硅基动感的糖血酮尿酸分析仪说明书",
    "美的家用热水器说明书",
    "大宏光说明书",
    "Instant pot 菜谱书和说明书"
]

staging = []
for name in items_list:
    staging.append({
        "name": name,
        "category": "📚 文档资产",
        "sub_category": "说明书与保修卡",
        "category_record_id": cat_id,
        "space_record_id": space_id,
        "location": "暂存区",
        "container": "说明书文件袋",
        "id": None,
        "quantity": 1,
        "status": ["盘点中"]
    })

os.makedirs("data/staging", exist_ok=True)
with open("data/staging/staging_items.json", "w", encoding="utf-8") as f:
    json.dump({"items": staging}, f, ensure_ascii=False, indent=2)

print("==== 待推送盘点清单 (纯文本格式) ====")
print("**大分类：📚 文档资产**")
print("**子分类：说明书与保修卡**")
print("**所在位置：说明书文件袋**\n")
print("包含以下物品：")
for i, item in enumerate(items_list, 1):
    print(f"{i}. {item}（数量：1）")
print("====================================")
