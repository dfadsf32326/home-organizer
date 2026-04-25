import json

with open("data/staging/staging_items.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("==== 待推送盘点清单预览 ====")
for idx, item in enumerate(data.get("items", []), 1):
    print(f"{idx}. 名称: {item['name']}")
    print(f"   分类: {item['category']} / {item['sub_category']}")
    print(f"   数量: {item['quantity']}")
    print("-" * 30)

