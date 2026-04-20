import json
import subprocess
import os
from datetime import datetime

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
TABLE_ID = "tbluMVXBpHIJDGyi"
ITEMS_FILE = "/Users/robinlu/Self-established_skill/home-organizer/data/items.json"

def find_all_items(obj, items_list):
    if isinstance(obj, dict):
        if "items" in obj and isinstance(obj["items"], list):
            items_list.extend(obj["items"])
        for key in obj:
            find_all_items(obj[key], items_list)
    elif isinstance(obj, list):
        for item in obj:
            find_all_items(item, items_list)

def get_feishu_data():
    """获取飞书当前所有数据，建立 本地数据库ID -> (updated_at, record_id) 映射"""
    cmd = [
        LARK_CLI, "base", "+record-list",
        "--base-token", BASE_TOKEN,
        "--table-id", TABLE_ID,
        "--limit", "500"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {}
    
    feishu_map = {}
    try:
        raw_data = json.loads(result.stdout)
        records = raw_data.get("data", {}).get("records", []) or raw_data.get("data", {}).get("items", [])
        for rec in records:
            fields = rec.get("fields", {})
            rid = rec.get("id") or rec.get("record_id")
            item_id = fields.get("本地数据库ID")
            updated_at = fields.get("更新时间")
            if item_id:
                feishu_map[item_id] = {"updated_at": updated_at, "record_id": rid}
    except Exception as e:
        print(f"Error parsing Feishu data: {e}")
    return feishu_map

def parse_iso(dt_str):
    if not dt_str: return 0
    try:
        return datetime.fromisoformat(dt_str).timestamp()
    except:
        try: return float(dt_str) / 1000 if len(str(dt_str)) > 10 else float(dt_str)
        except: return 0

def sync():
    with open(ITEMS_FILE, 'r', encoding='utf-8') as f:
        local_data = json.load(f)

    local_items = []
    find_all_items(local_data, local_items)
    
    feishu_data = get_feishu_data()
    
    synced_count = 0
    to_update_batch = []

    for item in local_items:
        iid = item.get("id")
        local_ts = parse_iso(item.get("updated_at"))
        
        fs_info = feishu_data.get(iid)
        if fs_info:
            fs_ts = parse_iso(fs_info["updated_at"])
            if local_ts > fs_ts:
                to_update_batch.append({
                    "record_id": fs_info["record_id"],
                    "fields": {
                        "物品名称": item.get("name"),
                        "大类": [item.get("category")],
                        "子分类": item.get("sub_category"),
                        "位置": item.get("location"),
                        "容器": item.get("container"),
                        "本地数据库ID": item.get("id"),
                        "状态": [item.get("status", "active")]
                    }
                })
        else:
            # 自动创建逻辑：如果飞书没有这个 ID，则 upsert
            to_update_batch.append({
                "record_id": None,
                "fields": {
                    "物品名称": item.get("name"),
                    "大类": [item.get("category")],
                    "子分类": item.get("sub_category"),
                    "位置": item.get("location"),
                    "容器": item.get("container"),
                    "本地数据库ID": item.get("id"),
                    "状态": [item.get("status", "active")]
                }
            })

    if to_update_batch:
        for entry in to_update_batch:
            if entry["record_id"]:
                cmd = [
                    LARK_CLI, "base", "+record-update",
                    "--base-token", BASE_TOKEN,
                    "--table-id", TABLE_ID,
                    "--record-id", entry["record_id"],
                    "--fields", json.dumps(entry["fields"], ensure_ascii=False)
                ]
            else:
                cmd = [
                    LARK_CLI, "base", "+record-upsert",
                    "--base-token", BASE_TOKEN,
                    "--table-id", TABLE_ID,
                    "--json", json.dumps(entry["fields"], ensure_ascii=False)
                ]
            subprocess.run(cmd, capture_output=True)
            synced_count += 1

    print(f"Sync complete. Processed {synced_count} items with mapping '本地数据库ID'.")

if __name__ == "__main__":
    sync()
