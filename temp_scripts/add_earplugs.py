import json

staging_file = "/Users/robinlu/.hermes/skills/custom/home-organizer/data/staging/staging_items.json"
with open(staging_file, "r") as f:
    data = json.load(f)

new_items = [
    {
      "id": "staging_611",
      "name": "蜜蜡耳塞",
      "sub_category": "护理工具",
      "category_record_id": "recvhlcSNSLL4D",
      "container": "衣柜左下收纳箱",
      "space_record_id": "recvi5QBTv09x4",
      "remark": "1对",
      "status": ["盘点中"]
    },
    {
      "id": "staging_612",
      "name": "安尔优耳塞",
      "sub_category": "护理工具",
      "category_record_id": "recvhlcSNSLL4D",
      "container": "衣柜左下收纳箱",
      "space_record_id": "recvi5QBTv09x4",
      "remark": "1对",
      "status": ["盘点中"]
    },
    {
      "id": "staging_613",
      "name": "胶泥耳塞",
      "sub_category": "护理工具",
      "category_record_id": "recvhlcSNSLL4D",
      "container": "衣柜左下收纳箱",
      "space_record_id": "recvi5QBTv09x4",
      "remark": "1对",
      "status": ["盘点中"]
    }
]

data["items"].extend(new_items)

with open(staging_file, "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Added 3 earplug items successfully")
