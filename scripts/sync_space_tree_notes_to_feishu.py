#!/usr/bin/env python3
"""
将本地 space_tree.json 的备注推送到飞书空间表
"""

import json
import subprocess
import os

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
SPACE_TABLE_ID = "tbl2cA30WNdkjsLS"
PROJECT_ROOT = "/Users/robinlu/Self-established_skill/home-organizer"
SPACE_TREE_FILE = os.path.join(PROJECT_ROOT, "data", "space_tree.json")

def get_feishu_records():
    cmd = [LARK_CLI, "base", "+record-list", 
           "--base-token", BASE_TOKEN, 
           "--table-id", SPACE_TABLE_ID, 
           "--limit", "500"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        return {}
    
    mapping = {}
    data = json.loads(res.stdout).get("data", {})
    records = data.get("data", [])
    fields = data.get("fields", [])
    record_ids = data.get("record_id_list", [])
    
    try:
        name_idx = fields.index("容器名")
    except ValueError:
        return {}
        
    for i, row in enumerate(records):
        name = row[name_idx]
        if isinstance(name, list): name = name[0]
        if name:
            mapping[name] = record_ids[i]
            
    return mapping

def main():
    with open(SPACE_TREE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    nodes = data.get("nodes", [])
    
    remote_map = get_feishu_records()
    
    print("\n📤 正在推送备注字段到飞书...")
    
    updated = 0
    for node in nodes:
        name = node.get("name")
        notes = node.get("notes")
        
        if not notes:
            continue
            
        record_id = remote_map.get(name)
        
        if record_id:
            fields = {
                "备注": notes
            }
            cmd = [LARK_CLI, "base", "+record-upsert",
                   "--base-token", BASE_TOKEN,
                   "--table-id", SPACE_TABLE_ID,
                   "--record-id", record_id,
                   "--json", json.dumps(fields, ensure_ascii=False)]
            
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                 updated += 1
                 print(f"  📝 备注更新成功: {name}")
            else:
                 print(f"  ❌ 备注更新失败 {name}: {res.stderr.strip()}")

    print(f"\n📊 操作完成，共更新 {updated} 条记录的备注。")

if __name__ == '__main__':
    main()
