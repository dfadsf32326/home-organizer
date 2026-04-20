import json
import subprocess
import os
from datetime import datetime

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
TABLE_ID = "tbluMVXBpHIJDGyi"
ITEMS_FILE = "/Users/robinlu/Self-established_skill/home-organizer/data/items.json"

def get_feishu_map():
    """获取飞书数据，建立 本地数据库ID -> {record_id, updated_at} 的映射"""
    cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--limit", "1000"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0: return {}
    
    feishu_map = {}
    try:
        data = json.loads(result.stdout)
        records = data.get("data", {}).get("records", []) or data.get("data", {}).get("items", [])
        for rec in records:
            fields = rec.get("fields", {})
            rid = rec.get("id") or rec.get("record_id")
            local_id = fields.get("本地数据库ID")
            if local_id:
                # 如果发现重复的本地数据库ID，记录下所有的 record_id 以便后续清理
                if local_id not in feishu_map:
                    feishu_map[local_id] = []
                feishu_map[local_id].append({
                    "record_id": rid,
                    "updated_at": fields.get("更新时间"),
                    "item_name": fields.get("物品名称")
                })
    except: pass
    return feishu_map

def sync_item(item, feishu_records):
    """同步单个物品，处理重复、更新和创建"""
    local_ts = datetime.fromisoformat(item.get("updated_at", "1970-01-01")).timestamp()
    
    # 构造字段
    fields = {
        "物品名称": item.get("name"),
        "大类": [item.get("category")],
        "子分类": item.get("sub_category"),
        "位置": item.get("location"),
        "容器": item.get("container"),
        "本地数据库ID": item.get("id"),
        "状态": [item.get("status", "active")]
    }

    if feishu_records:
        # 1. 处理重复：保留最新的一条，删除其他的
        sorted_records = sorted(feishu_records, key=lambda x: x['updated_at'] or "", reverse=True)
        keep_record = sorted_records[0]
        
        # 删除重复项
        for old in sorted_records[1:]:
            subprocess.run([LARK_CLI, "base", "+record-delete", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--record-id", old["record_id"], "--yes"], capture_output=True)
        
        # 2. 检查是否需要更新内容
        # 这里简单起见直接 update 以同步最新的本地 ID 映射，或比对时间戳
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
        # 3. 飞书不存在，执行创建
        cmd = [
            LARK_CLI, "base", "+record-upsert",
            "--base-token", BASE_TOKEN,
            "--table-id", TABLE_ID,
            "--json", json.dumps(fields, ensure_ascii=False)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        try:
            # 获取新创建的 record_id 并保存回本地
            new_data = json.loads(res.stdout)
            return new_data["data"]["record_id_list"][0]
        except: return None

def main():
    with open(ITEMS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    feishu_map = get_feishu_map()
    
    def process_node(node):
        if isinstance(node, dict):
            if "items" in node:
                for item in node["items"]:
                    rid = sync_item(item, feishu_map.get(item.get("id")))
                    if rid: item["feishu_record_id"] = rid
            for v in node.values(): process_node(v)
        elif isinstance(node, list):
            for i in node: process_node(i)

    process_node(data)
    
    # 写回 items.json 以持久化 feishu_record_id
    with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Sync and Deduplication complete.")

if __name__ == "__main__":
    main()
