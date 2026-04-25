import json

with open("data/items.json", "r", encoding="utf-8") as f:
    items = json.load(f)
    
if isinstance(items, dict):
    item_list = items.values()
else:
    item_list = items

found = []
for item in item_list:
    space = item.get("space")
    if space in ["家人病历袋", "保险合同袋子", "我的病历相关文件袋", "工作与合同文件袋"]:
        print(f"[{space}] {item.get('name')}")
        found.append(item)
print(f"Total found: {len(found)}")
