import json

staging_file = "/Users/robinlu/.hermes/skills/custom/home-organizer/data/staging/staging_items.json"
with open(staging_file, "r") as f:
    data = json.load(f)

# 删除"未命名物品"那条记录
data["items"] = [item for item in data["items"] if item["id"] != "staging_306"]

with open(staging_file, "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Removed successfully")
