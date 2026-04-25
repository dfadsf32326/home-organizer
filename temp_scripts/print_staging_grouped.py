import json

with open("data/staging/staging_items.json", "r", encoding="utf-8") as f:
    data = json.load(f)

grouped = {}
for item in data.get("items", []):
    major = item['category']
    minor = item['sub_category']
    if major not in grouped:
        grouped[major] = {}
    if minor not in grouped[major]:
        grouped[major][minor] = []
    grouped[major][minor].append(f"{item['name']} (x{item['quantity']})")

print("==== 待推送盘点清单 (按分类汇总) ====")
for major, minors in grouped.items():
    print(f"📦 【{major}】")
    for minor, items in minors.items():
        print(f"  ├─ 📂 {minor}")
        for name in items:
            print(f"  │  └─ {name}")
print("====================================")
