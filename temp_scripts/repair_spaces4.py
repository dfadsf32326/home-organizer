import json

with open("temp_scripts/repair_spaces4.json", "r", encoding="utf-8") as f:
    res = json.load(f)

data_list = res.get("data", {}).get("data", [])
print(f"Total spaces fetched: {len(data_list)}")

name_idx = None
rid_idx = None
if len(data_list) > 0:
    for i, val in enumerate(data_list[0]):
        if isinstance(val, str) and val.startswith("recv"):
            rid_idx = i
        # 根据经验猜测名字字段
        if isinstance(val, str) and val in ["暂存区", "我的病历相关文件袋", "客厅", "我的病历相关文件夹", "书房"]:
            name_idx = i
            
if name_idx is None:
    # 回退到硬编码
    name_idx = 1
    rid_idx = 6

print(f"Indices: Name={name_idx}, RID={rid_idx}")
for row in data_list:
    rid = row[rid_idx]
    name = row[name_idx]
    if rid in ["recvhN14HPrYMU", "recvhMXUk94xEj"]:
        print(f"Found match: {name} -> {rid}")
