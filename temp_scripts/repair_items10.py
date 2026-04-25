import json

with open("data/items.json", "r", encoding="utf-8") as f:
    items = json.load(f)
    
item_list = []
if isinstance(items, dict):
    if "items" in items:
        item_list = items["items"]
    elif "data" in items and "items" in items["data"]:
        item_list = items["data"]["items"]
    else:
        for k, v in items.items():
            if isinstance(v, list):
                item_list.extend(v)
            else:
                item_list.append(v)
elif isinstance(items, list):
    for i in items:
        if isinstance(i, list):
            for sub_i in i:
                item_list.append(sub_i)
        else:
            item_list.append(i)

found = []
for item in item_list:
    if not isinstance(item, dict): continue
    space = item.get("space")
    name = item.get("name")
    if space in ["家人病历袋", "保险合同袋子", "我的病历相关文件袋", "工作与合同文件袋"]:
        print(f"[{space}] {name}")
        found.append(item)
print(f"Total found: {len(found)}")

if len(found) > 0:
    with open("temp_scripts/need_fix_items.json", "w", encoding="utf-8") as fw:
        json.dump(found, fw, ensure_ascii=False, indent=2)

