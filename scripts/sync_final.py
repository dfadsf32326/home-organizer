import json
import subprocess
import os
from datetime import datetime

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
TABLE_ID = "tbluMVXBpHIJDGyi"
ITEMS_FILE = "/Users/robinlu/Self-established_skill/home-organizer/data/items.json"
SPACE_MAP_FILE = "/Users/robinlu/Self-established_skill/home-organizer/data/space_map.json"

def get_feishu_records():
    """全量获取飞书记录，返回 本地数据库ID -> record_id 的映射"""
    cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--limit", "500"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        return {}
    
    mapping = {}
    try:
        data = json.loads(res.stdout).get("data", {})
        records = data.get("data", [])
        field_names = data.get("fields", [])
        record_ids = data.get("record_id_list", [])
        
        id_idx = field_names.index("本地数据库ID") if "本地数据库ID" in field_names else None
        if id_idx is not None:
            for i, row in enumerate(records):
                local_id = row[id_idx] if id_idx < len(row) else None
                if local_id:
                    if local_id not in mapping:
                        mapping[local_id] = []
                    mapping[local_id].append(record_ids[i])
    except:
        pass
    return mapping

def sync():
    if not os.path.exists(ITEMS_FILE):
        print("Error: items.json missing")
        return

    with open(ITEMS_FILE, 'r', encoding='utf-8') as f:
        items_data = json.load(f)
    
    items_list = items_data.get("items", [])
    print(f"Starting sync for {len(items_list)} items...")

    feishu_map = get_feishu_records()
    
    success_count = 0
    for item in items_list:
        local_id = item.get("id")
        fields = {
            "物品名称": item.get("name"),
            "大类": [item.get("category")] if item.get("category") else [],
            "子分类": item.get("sub_category"),
            "位置": item.get("location"),
            "容器": item.get("container"),
            "本地数据库ID": local_id,
            "状态": [item.get("status", "active")]
        }

        if local_id in feishu_map:
            rids = feishu_map[local_id]
            target_rid = rids[0]
            
            if len(rids) > 1:
                for extra_rid in rids[1:]:
                    subprocess.run([LARK_CLI, "base", "+record-delete", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--record-id", extra_rid, "--yes"])

            cmd = [
                LARK_CLI, "base", "+record-update",
                "--base-token", BASE_TOKEN,
                "--table-id", TABLE_ID,
                "--record-id", target_rid,
                "--fields", json.dumps(fields, ensure_ascii=False)
            ]
        else:
            cmd = [
                LARK_CLI, "base", "+record-upsert",
                "--base-token", BASE_TOKEN,
                "--table-id", TABLE_ID,
                "--json", json.dumps(fields, ensure_ascii=False)
            ]
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            try:
                rid_data = json.loads(res.stdout)
                res_data = rid_data.get("data", {})
                # +record-update returns { "data": { "record": { ... } } }
                # +record-upsert returns { "data": { "record_id_list": [...] } }
                new_rid = res_data.get("record_id_list", [None])[0] or res_data.get("record", {}).get("record_id")
                if new_rid:
                    item["feishu_record_id"] = new_rid
                    item["updated_at"] = datetime.now().isoformat()
                    success_count += 1
            except:
                pass
        
    with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(items_data, f, ensure_ascii=False, indent=2)
    
    print(f"Sync finished. {success_count} items updated/created.")

if __name__ == "__main__":
    sync()
