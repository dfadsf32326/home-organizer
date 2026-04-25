import json

with open("data/space_tree.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("==== 相关空间搜索结果 ====")
for node in data.get("nodes", []):
    name = node.get("name", "")
    if "病" in name or "袋" in name or "文件" in name:
        print(f"Name: {name}, ID: {node.get('id')}, Record_ID: {node.get('record_id')}")

