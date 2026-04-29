import json

staging_file = "/Users/robinlu/.hermes/skills/custom/home-organizer/data/staging/staging_items.json"
with open(staging_file, "r") as f:
    data = json.load(f)

for item in data["items"]:
    if item["name"] == "吉列剃须刀替换刀头":
        item["sub_category"] = "身体洗护"
        item["category_record_id"] = "recvhlcRUjNcMt"

with open(staging_file, "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Updated successfully")
