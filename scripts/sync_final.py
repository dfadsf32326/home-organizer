import json
import subprocess
import os
from datetime import datetime

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
TABLE_ID = "tbluMVXBpHIJDGyi"
ITEMS_FILE = "/Users/robinlu/Self-established_skill/home-organizer/data/items.json"

def get_feishu_map():
    """获取飞书数据，建立 本地数据库ID -> [{record_id, updated_at, item_name}] 的映射"""
    # 使用 --limit 500 尽量一次获取全量数据
    cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--limit", "500"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0: 
        print(f"Error fetching Feishu data: {result.stderr}")
        return {}
    
    feishu_map = {}
    try:
        raw_data = json.loads(result.stdout)
        data_block = raw_data.get("data", {})
        records = data_block.get("data", [])
        field_names = data_block.get("fields", [])
        record_ids = data_block.get("record_id_list", [])
        
        # 建立字段名到索引的映射
        field_idx = {name: i for i, name in enumerate(field_names)}
        id_idx = field_idx.get("本地数据库ID")
        ts_idx = field_idx.get("更新时间")
        name_idx = field_idx.get("物品名称")

        for i, row in enumerate(records):
            rid = record_ids[i]
            local_id = row[id_idx] if id_idx is not None and id_idx < len(row) else None
            
            if local_id:
                if local_id not in feishu_map:
                    feishu_map[local_id] = []
                feishu_map[local_id].append({
                    "record_id": rid,
                    "updated_at": row[ts_idx] if ts_idx is not None and ts_idx < len(row) else "",
                    "item_name": row[name_idx] if name_idx is not None and name_idx < len(row) else ""
                })
    except Exception as e:
        print(f"Parsing error: {e}")
    return feishu_map

def sync_item(item, feishu_records):
    """同步单个物品，处理重复、更新和创建"""
    # 构造字段
    fields = {
        "物品名称": item.get("name"),
        "大类": [item.get("category")] if item.get("category") else [],
        "子分类": item.get("sub_category"),
        "位置": item.get("location"),
        "容器": item.get("container"),
        "本地数据库ID": item.get("id"),
        "状态": [item.get("status", "active")]
    }

    if feishu_records:
        # 1. 处理重复：保留最新的一条，删除其他的
        # 过滤掉更新时间为空的情况，按字符串排序即可（ISO格式）
        sorted_records = sorted(feishu_records, key=lambda x: x['updated_at'] or "", reverse=True)
        keep_record = sorted_records[0]
        
        # 删除重复项
        for old in sorted_records[1:]:
            print(f"Deleting duplicate: {old['item_name']} ({old['record_id']})")
            subprocess.run([LARK_CLI, "base", "+record-delete", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--record-id", old["record_id"], "--yes"], capture_output=True)
        
        # 2. 更新保留的那条记录
        # 这里为了确保 ID 映射正确，即使时间戳没变也进行一次 upsert/update
        cmd = [
            LARK_CLI, "base", "+record-update",
            "--base-token", BASE_TOKEN,
            "--table-id", TABLE_ID,
            "--record-id", keep_record["record_id"],
            "--fields", json.dumps(fields, ensure_ascii=False)
        ]
        subprocess.run(cmd, capture_output=True)
        return keep_record["record_id"]
    else:
        # 3. 飞书不存在该 ID，执行创建
        print(f"Creating new record in Feishu: {item.get('name')}")
        cmd = [
            LARK_CLI, "base", "+record-upsert",
            "--base-token", BASE_TOKEN,
            "--table-id", TABLE_ID,
            "--json", json.dumps(fields, ensure_ascii=False)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        try:
            new_data = json.loads(res.stdout)
            return new_data["data"]["record_id_list"][0]
        except Exception as e:
            print(f"Upsert error for {item.get('name')}: {e}")
            return None

def main():
    if not os.path.exists(ITEMS_FILE):
        print("Items file not found.")
        return

    with open(ITEMS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("Fetching Feishu records...")
    feishu_map = get_feishu_map()
    print(f"Found {len(feishu_map)} unique local IDs in Feishu.")
    
    sync_count = 0
    def process_node(node):
        nonlocal sync_count
        if isinstance(node, dict):
            if "items" in node:
                for item in node["items"]:
                    rid = sync_item(item, feishu_map.get(item.get("id")))
                    if rid: 
                        item["feishu_record_id"] = rid
                        sync_count += 1
            for k, v in node.items():
                if k != "items": process_node(v)
        elif isinstance(node, list):
            for i in node: process_node(i)

    # 从 spaces 开始递归
    if "spaces" in data:
        process_node(data["spaces"])

    # 写回 items.json 以持久化 feishu_record_id
    with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Sync complete. Processed {sync_count} items.")

if __name__ == "__main__":
    main()
