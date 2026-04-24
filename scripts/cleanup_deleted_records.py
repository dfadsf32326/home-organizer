import json
import subprocess
import os

BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
SPACE_TABLE_ID = "tbl2cA30WNdkjsLS"
ITEM_TABLE_ID = "tbluMVXBpHIJDGyi"
LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")

def get_feishu_records(table_id):
    cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", table_id, "--limit", "1000"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        try:
            data = json.loads(res.stdout)
            records = data.get("data", {}).get("data", [])
            rids = []
            for r in records:
                if len(r) > 1 and isinstance(r[1], list) and len(r[1]) > 0:
                    rids.append(r[1][0].get("id"))
            return set(rids)
        except Exception as e:
            print(f"Error parsing json for table {table_id}: {e}")
            return None
    else:
        print(f"Error fetching from table {table_id}")
        return None

def cleanup_spaces():
    print("开始检查空间表 (Spaces)...")
    tree_file = "/Users/robinlu/Self-established_skill/home-organizer/data/space_tree.json"
    if not os.path.exists(tree_file):
        print("未找到 space_tree.json")
        return
        
    with open(tree_file, "r") as f:
        local_data = json.load(f)
    local_nodes = local_data.get("nodes", [])
    
    remote_rids = get_feishu_records(SPACE_TABLE_ID)
    if remote_rids is None:
        return
        
    new_nodes = []
    deleted = 0
    for node in local_nodes:
        rid = node.get("record_id")
        if rid and rid not in remote_rids:
            print(f"  🗑 发现飞书已删除记录，清理本地空间: {node.get('name')}")
            deleted += 1
        else:
            new_nodes.append(node)
            
    if deleted > 0:
        local_data["nodes"] = new_nodes
        with open(tree_file, "w", encoding="utf-8") as f:
            json.dump(local_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 成功从本地剔除了 {deleted} 条已在飞书云端删除的空间数据。")
    else:
        print("✅ 空间表本地数据干净，无残留脏数据。")

def cleanup_items():
    print("\n开始检查物品表 (Items)...")
    items_file = "/Users/robinlu/Self-established_skill/home-organizer/data/items.json"
    if not os.path.exists(items_file):
        print("未找到 items.json")
        return
        
    with open(items_file, "r") as f:
        items_data = json.load(f)
    local_items = items_data.get("items", [])
    
    remote_rids = get_feishu_records(ITEM_TABLE_ID)
    if remote_rids is None:
        return
        
    new_items = []
    deleted = 0
    for item in local_items:
        rid = item.get("feishu_record_id")
        if rid and rid not in remote_rids:
            print(f"  🗑 发现飞书已删除记录，清理本地物品: {item.get('name')}")
            deleted += 1
        else:
            new_items.append(item)
            
    if deleted > 0:
        items_data["items"] = new_items
        with open(items_file, "w", encoding="utf-8") as f:
            json.dump(items_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 成功从本地剔除了 {deleted} 条已在飞书云端删除的物品数据。")
    else:
        print("✅ 物品表本地数据干净，无残留脏数据。")

if __name__ == "__main__":
    cleanup_spaces()
    cleanup_items()
