import os
import json
import argparse
import uuid

def main():
    parser = argparse.ArgumentParser(description="Add a new space to space_map.json")
    parser.add_argument("--name", required=True, help="Space name")
    parser.add_argument("--parent", default="", help="Parent space name")
    parser.add_argument("--frequency", default="medium", help="Frequency of use (high/medium/low)")
    parser.add_argument("--type", default="container", help="Space type (surface/container/drawer/etc)")
    parser.add_argument("--activity", default="", help="Primary activity")
    parser.add_argument("--desc", default="", help="Description")
    
    args = parser.parse_args()
    
    # 路径配置
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    space_map_file = os.path.join(project_root, "data", "space_map.json")
    
    # 加载现有数据
    if os.path.exists(space_map_file):
        with open(space_map_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"spaces": []}
        
    spaces = data.get("spaces", [])
    
    # 防重检查
    for sp in spaces:
        if sp.get("name") == args.name:
            print(f"Error: Space with name '{args.name}' already exists.")
            return

    # 生成ID并构造新空间
    new_id = str(uuid.uuid4())[:8]
    # 这里也可以基于名字生成拼音ID，但UUID足够用作唯一标识
    new_space = {
        "id": new_id,
        "name": args.name,
        "parent": args.parent,
        "frequency": args.frequency,
        "type": args.type,
        "primary_activity": args.activity,
        "description": args.desc,
        "status": "inventory_pending"
    }
    
    spaces.append(new_space)
    data["spaces"] = spaces
    
    with open(space_map_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully added new space: {args.name} (ID: {new_id})")

if __name__ == "__main__":
    main()
