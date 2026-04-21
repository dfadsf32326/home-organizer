#!/usr/bin/env python3
"""
将本地 space_map.json 推送到飞书空间表，包含父记录逻辑
"""

import json
import subprocess
import os
import time

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
SPACE_TABLE_ID = "tbl2cA30WNdkjsLS"
PROJECT_ROOT = "/Users/robinlu/Self-established_skill/home-organizer"
SPACE_MAP_FILE = os.path.join(PROJECT_ROOT, "data", "space_map.json")

def get_feishu_records():
    """获取目前飞书中已有的记录，用来构建 名字 -> record_id 的映射"""
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

def flatten_space_map():
    with open(SPACE_MAP_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    spaces = data.get('spaces', [])
    mapping = {}
    for space in spaces:
        space_id = space.get('id')
        space_name = space.get('name', '')
        parent = space.get('parent', '')
        
        if space_id:
            mapping[space_id] = {
                'id': space_id,
                'name': space_name,
                'parent_name': parent
            }
        
        if 'containers' in space:
            for container in space['containers']:
                container_id = f"{space_name}-{container['name']}"
                mapping[container_id] = {
                    'id': container_id,
                    'name': container['name'],
                    'parent_name': space_name
                }
    return mapping

def main():
    mapping = flatten_space_map()
    remote_map = get_feishu_records()
    
    print("\n📤 正在更新父级关联到飞书...")
    
    updated = 0
    for space_id, info in mapping.items():
        name = info.get("name")
        parent_name = info.get("parent_name")
        
        if not parent_name:
            continue
            
        record_id = remote_map.get(name)
        parent_record_id = remote_map.get(parent_name)
        
        if record_id and parent_record_id:
            # 更新此记录的 父记录 2 字段
            fields = {
                "父记录 2": [parent_record_id]
            }
            cmd = [LARK_CLI, "base", "+record-upsert",
                   "--base-token", BASE_TOKEN,
                   "--table-id", SPACE_TABLE_ID,
                   "--record-id", record_id,
                   "--json", json.dumps(fields, ensure_ascii=False)]
            
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                 updated += 1
                 print(f"  🔗 关联成功: {name} -> {parent_name}")
            else:
                 print(f"  ❌ 关联失败 {name}: {res.stderr.strip()}")
            time.sleep(0.1)

    print(f"\n📊 操作完成，共关联 {updated} 条记录。")

if __name__ == '__main__':
    main()
