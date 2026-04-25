import json

with open("data/staging/staging_items.json", "r", encoding="utf-8") as f:
    data = json.load(f)

if data.get("items"):
    print("==== 示例数据结构 (第一条) ====")
    print(json.dumps(data["items"][0], ensure_ascii=False, indent=2))
else:
    print("暂存区没有数据")
