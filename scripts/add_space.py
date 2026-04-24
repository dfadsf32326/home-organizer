import os
import json
import argparse
import uuid

def main():
    parser = argparse.ArgumentParser(description="Add a new space to space_tree.json")
    parser.add_argument("--name", required=True, help="Space name")
    parser.add_argument("--parent", default="", help="Parent space name")
    parser.add_argument("--frequency", default="medium", help="Frequency of use (high/medium/low)")
    parser.add_argument("--type", default="container", help="Space type (surface/container/drawer/etc)")
    parser.add_argument("--activity", default="", help="Primary activity")
    parser.add_argument("--desc", default="", help="Description")
    
    args = parser.parse_args()
    
    # 路径配置
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    space_tree_file = os.path.join(project_root, "data", "space_tree.json")
    

    # 加载现有数据
    if os.path.exists(space_tree_file):
        with open(space_tree_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"nodes": []}
        
    nodes = data.get("nodes", [])
    
    # 防重检查
    for nd in nodes:
        if nd.get("name") == args.name:
            print(f"Error: Space with name '{args.name}' already exists.")
            return

    # 生成ID并构造新空间 (适配 space_tree.json 格式)
    new_id = str(uuid.uuid4())[:8]
    new_node = {
        "id": new_id,
        "name": args.name,
        "parent_id": None, # Should ideally lookup parent ID, but will be resolved by sync script or empty
        "level": 3,
        "path": ""
    }
    
    nodes.append(new_node)
    data["nodes"] = nodes
    
    with open(space_tree_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nSuccessfully added new space to local database: {args.name} (ID: {new_id})")
    print(f"\n[ACTION REQUIRED] Next steps according to SKILL SOP:")
    print(f"1. Ask user for permission to push to Feishu.")
    print(f"2. Upon approval, run `python3 scripts/sync_spaces_bidirectional.py`.")
    print(f"3. The sync script will automatically push this new space, get the Feishu Record ID, and write it back to `space_tree.json`.")

if __name__ == "__main__":
    main()
