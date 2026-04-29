import json

staging_file = "/Users/robinlu/.hermes/skills/custom/home-organizer/data/staging/staging_items.json"
with open(staging_file, "r") as f:
    data = json.load(f)

for item in data["items"]:
    if item["name"] in ["吉列剃须刀替换刀头", "制作唇膏用的唇膏管", "白蜂蜡"]:
        item["sub_category"] = "护肤与美妆"
        item["category_record_id"] = "recvhlcSek6XIu"

with open(staging_file, "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Updated successfully")
