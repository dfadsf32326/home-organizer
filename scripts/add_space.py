import os
import json
import argparse
import subprocess
import sys

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
SPACE_TABLE_ID = "tbl2cA30WNdkjsLS"
SPACE_TREE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "space_tree.json")

def load_spaces():
    if not os.path.exists(SPACE_TREE_FILE):
        return []
    with open(SPACE_TREE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("data", [])

def main():
    parser = argparse.ArgumentParser(description="Add a new space to Feishu and sync locally")
    parser.add_argument("--name", required=True, help="Space name")
    parser.add_argument("--parent", default="", help="Parent space name")
    
    args = parser.parse_args()
    
    existing_spaces = load_spaces()
    for sp in existing_spaces:
        if sp.get("name") == args.name:
            print(f"Error: Space with name '{args.name}' already exists in local database.")
            sys.exit(1)

    parent_rid = None
    if args.parent:
        for sp in existing_spaces:
            if sp.get("name") == args.parent:
                parent_rid = sp.get("record_id")
                break
        if not parent_rid:
            print(f"Warning: Parent space '{args.parent}' not found. Will create at root level.")

    fields = {
        "fld3jffiay": args.name
    }
    
    if parent_rid:
        fields["fld69LXYnd"] = [{"id": parent_rid}]
        
    print(f"Pushing new space '{args.name}' to Feishu...")
    
    cmd = [
        LARK_CLI, "base", "+record-upsert", 
        "--base-token", BASE_TOKEN, 
        "--table-id", SPACE_TABLE_ID, 
        "--json", json.dumps(fields, ensure_ascii=False)
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Failed to push to Feishu. Error: {res.stderr}\nStdout: {res.stdout}")
        sys.exit(1)
        
    print("✅ Successfully pushed to Feishu.")
    
    print("Syncing local data...")
    sync_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sync_spaces_down.py")
    subprocess.run(["python3", sync_script])

if __name__ == "__main__":
    main()
