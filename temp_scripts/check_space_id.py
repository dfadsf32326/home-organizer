import json

with open("data/space_tree.json", "r", encoding="utf-8") as f:
    space_tree = json.load(f)

spaces = []
if isinstance(space_tree, dict):
    if "children" in space_tree:
        spaces = [space_tree]
    else:
        for k, v in space_tree.items():
            spaces.append(v)
elif isinstance(space_tree, list):
    spaces = space_tree

def find_rid(node):
    target_ids = ["recvhN14HPrYMU", "recvhMXUk94xEj", "recvhOuiRVy6fN", "recvhOujaqCXdL"]
    rid = node.get("record_id")
    if rid in target_ids:
        print(f"Found Space: {node.get('name')} -> RID: {rid}")
    
    if "children" in node and isinstance(node["children"], list):
        for c in node["children"]:
            find_rid(c)

for s in spaces:
    find_rid(s)

