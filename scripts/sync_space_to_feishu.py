#!/usr/bin/env python3
"""
将本地 space_map.json 推送到飞书空间表
"""

import json
import subprocess
import os

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
SPACE_TABLE_ID = "tbl2cA30WNdkjsLS"
PROJECT_ROOT = "/Users/robinlu/Self-established_skill/home-organizer"
SPACE_MAP_FILE = os.path.join(PROJECT_ROOT, "data", "space_map.json")

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
    
    print("\n📤 正在推送数据到飞书...")
    # 这里我们只推送 容器名
    
    created = 0
    for space_id, info in mapping.items():
        fields = {
            "容器名": info.get("name", "")
        }
        
        # 使用upsert的话，需要有一个主键，但是目前飞书表中只有 容器名。
        # 我们这里简单做插入
        cmd = [LARK_CLI, "base", "+record-upsert",
               "--base-token", BASE_TOKEN,
               "--table-id", SPACE_TABLE_ID,
               "--json", json.dumps(fields, ensure_ascii=False)]
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
             created += 1
             print(f"  ✅ 创建/更新: {info.get('name')}")
        else:
             print(f"  ❌ 失败 {info.get('name')}: {res.stderr.strip()}")

    print(f"\n📊 操作完成，共处理 {created} 条记录。")

if __name__ == '__main__':
    main()
