import json

with open("data/category_mapping.json", "r", encoding="utf-8") as f:
    cats = json.load(f)

for minor, info in cats.items():
    if any(keyword in minor for keyword in ["纪念", "证件", "照片", "首饰", "配饰", "办公"]):
        print(f"Sub-category: {minor}, Major: {info.get('major')}, ID: {info.get('record_id')}")
