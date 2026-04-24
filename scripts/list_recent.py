import os
import json

with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/items.json"), "r") as f:
    data = json.load(f)

recent_items = []
for item in data.get("items", []):
    if item.get("container_id") == "手机电子产品配件箱" or item.get("container") == "手机电子产品配件箱":
        recent_items.append(item)

# Group by sub_category
grouped = {}
for item in recent_items:
    sub = item.get("sub_category", "未分类")
    if sub not in grouped:
        grouped[sub] = []
    grouped[sub].append(item["name"])

for sub, names in grouped.items():
    print(f"【{sub}】")
    for name in names:
        print(f" - {name}")
