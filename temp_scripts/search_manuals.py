import json

with open("data/category_mapping.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for minor, info in data.items():
    if "书" in minor or "册" in minor or "说明" in minor or info["major"] == "📚 文档资产":
        print(f"Minor: {minor}, Major: {info['major']}, Record_ID: {info['record_id']}")
