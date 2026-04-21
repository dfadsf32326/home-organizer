#!/usr/bin/env python3
"""
空间表双向同步脚本

功能：
1. 本地 → 飞书：将 space_mapping.json 中的空间推送到飞书空间表
2. 飞书 → 本地：从飞书空间表拉取数据更新 space_mapping.json

使用方式：
  python sync_space_map.py --push    # 本地推送飞书
  python sync_space_map.py --pull    # 飞书拉取本地
  python sync_space_map.py --sync    # 双向同步（先pull再push）
"""

import json
import subprocess
import os
import argparse
from datetime import datetime

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
SPACE_TABLE_ID = "tbl2cA30WNdkjsLS"
PROJECT_ROOT = "/Users/robinlu/Self-established_skill/home-organizer"
MAPPING_FILE = os.path.join(PROJECT_ROOT, "data", "space_mapping.json")
SPACE_MAP_FILE = os.path.join(PROJECT_ROOT, "data", "space_map.json")


def load_local_mapping():
    """加载本地映射字典"""
    if not os.path.exists(MAPPING_FILE):
        print("⚠️  本地映射文件不存在，将创建空字典")
        return {}
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_local_mapping(mapping):
    """保存本地映射字典"""
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"✅ 本地映射已保存到 {MAPPING_FILE}")


def flatten_space_map():
    """
    从 space_map.json 提取所有空间/容器，扁平化为 mapping 格式
    """
    if not os.path.exists(SPACE_MAP_FILE):
        print(f"❌ 源文件不存在: {SPACE_MAP_FILE}")
        return {}
    
    with open(SPACE_MAP_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    spaces = data.get('spaces', [])
    mapping = {}
    
    for space in spaces:
        space_id = space.get('id')
        space_name = space.get('name', '')
        space_type = space.get('type', '未指定')
        parent = space.get('parent', '')
        
        # 有 id 的记录直接处理
        if space_id:
            mapping[space_id] = {
                'record_id': '',
                'name': space_name,
                'parent': parent or '',
                'type': space_type,
                'frequency': space.get('frequency', ''),
                'status': space.get('status', ''),
                'primary_activity': space.get('primary_activity', ''),
                'description': space.get('description') or space.get('notes', '')
            }
        
        # 处理嵌套的 containers（room 类型）
        if 'containers' in space:
            for container in space['containers']:
                # 生成唯一 id：父空间名-容器名
                container_id = f"{space_name}-{container['name']}"
                mapping[container_id] = {
                    'record_id': '',
                    'name': container['name'],
                    'parent': space_name,
                    'type': container.get('type', 'container'),
                    'frequency': '',
                    'status': '',
                    'primary_activity': '',
                    'description': ''
                }
    
    return mapping


def get_feishu_spaces():
    """从飞书空间表获取所有空间记录"""
    cmd = [LARK_CLI, "base", "+record-list", 
           "--base-token", BASE_TOKEN, 
           "--table-id", SPACE_TABLE_ID, 
           "--limit", "500"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    if res.returncode != 0:
        print(f"❌ 拉取飞书空间表失败: {res.stderr}")
        return {}
    
    remote_data = {}
    try:
        data_full = json.loads(res.stdout)
        data = data_full.get("data", {})
        records = data.get("data", [])
        field_names = data.get("fields", [])
        record_ids = data.get("record_id_list", [])
        
        idx_map = {name: i for i, name in enumerate(field_names)}
        
        # 字段：空间ID、空间名称、所属空间、空间类型、使用频率、盘点状态、主体活动、备注、记录ID
        for i, row in enumerate(records):
            rid = record_ids[i]
            
            def get_val(fname):
                idx = idx_map.get(fname)
                if idx is not None and idx < len(row):
                    val = row[idx]
                    # 处理列表类型返回值
                    if isinstance(val, list):
                        return val[0] if val else None
                    return val
                return None
            
            # 尝试获取空间ID字段，如果没有则用空间名称作为键
            space_id = get_val("空间ID") or get_val("空间名称")
            if space_id:
                remote_data[space_id] = {
                    'record_id': rid,
                    'name': get_val("空间名称") or '',
                    'parent': get_val("所属空间") or '',
                    'type': get_val("空间类型") or '',
                    'frequency': get_val("使用频率") or '',
                    'status': get_val("盘点状态") or '',
                    'primary_activity': get_val("主体活动") or '',
                    'description': get_val("备注") or ''
                }
    except Exception as e:
        print(f"❌ 解析飞书数据出错: {e}")
    
    return remote_data


def push_to_feishu(local_mapping):
    """将本地映射推送到飞书"""
    print("\n📤 推送本地空间到飞书...")
    
    remote_data = get_feishu_spaces()
    created = 0
    updated = 0
    
    for space_id, info in local_mapping.items():
        record_id = info.get("record_id", "")
        
        # 检查飞书是否已存在此空间ID
        if space_id in remote_data:
            # 已存在，补上 record_id（如果本地缺失）
            existing = remote_data[space_id]
            if existing.get("record_id") and not record_id:
                local_mapping[space_id]["record_id"] = existing["record_id"]
                print(f"  📝 补充 record_id: {space_id}")
            continue
        
        # 不存在，创建新记录
        fields = {
            "空间ID": space_id,
            "空间名称": info.get("name", ""),
            "所属空间": info.get("parent", ""),
            "空间类型": info.get("type", ""),
            "使用频率": info.get("frequency", ""),
            "盘点状态": info.get("status", ""),
            "主体活动": info.get("primary_activity", ""),
            "备注": info.get("description", "")
        }
        
        # 移除空值字段
        fields = {k: v for k, v in fields.items() if v}
        
        cmd = [LARK_CLI, "base", "+record-upsert",
               "--base-token", BASE_TOKEN,
               "--table-id", SPACE_TABLE_ID,
               "--json", json.dumps(fields, ensure_ascii=False)]
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            try:
                rj = json.loads(res.stdout)
                res_data = rj.get("data", {})
                new_rid = (res_data.get("record_id_list") or [None])[0] or \
                          res_data.get("record", {}).get("record_id")
                if new_rid:
                    local_mapping[space_id]["record_id"] = new_rid
                    created += 1
                    print(f"  ✅ 创建: {space_id} ({info.get('name')}) → {new_rid}")
            except Exception as e:
                print(f"  ⚠️  创建成功但解析返回值失败: {space_id} - {e}")
        else:
            print(f"  ❌ 创建失败 {space_id}: {res.stderr[:200]}")
    
    print(f"\n📊 推送完成：新建 {created} 条")
    return local_mapping


def pull_from_feishu(local_mapping):
    """从飞书拉取空间更新本地"""
    print("\n📥 从飞书拉取空间到本地...")
    
    remote_data = get_feishu_spaces()
    
    added = 0
    updated = 0
    
    for space_id, info in remote_data.items():
        record_id = info.get("record_id", "")
        
        if space_id not in local_mapping:
            # 本地不存在，新增
            local_mapping[space_id] = {
                'record_id': record_id,
                'name': info.get('name', ''),
                'parent': info.get('parent', ''),
                'type': info.get('type', ''),
                'frequency': info.get('frequency', ''),
                'status': info.get('status', ''),
                'primary_activity': info.get('primary_activity', ''),
                'description': info.get('description', '')
            }
            added += 1
            print(f"  ➕ 新增: {space_id} ({info.get('name')})")
        else:
            # 本地已存在，更新 record_id
            local_record_id = local_mapping[space_id].get("record_id", "")
            if record_id and local_record_id != record_id:
                local_mapping[space_id]["record_id"] = record_id
                updated += 1
                print(f"  🔄 更新 ID: {space_id}")
    
    print(f"\n📊 拉取完成：新增 {added} 条，更新 {updated} 条")
    return local_mapping


def sync():
    """双向同步：先拉取再推送"""
    local_mapping = load_local_mapping()
    
    # 如果本地为空，尝试从 space_map.json 初始化
    if not local_mapping:
        print("📋 本地映射为空，从 space_map.json 初始化...")
        local_mapping = flatten_space_map()
        print(f"  提取到 {len(local_mapping)} 条空间/容器记录")
    
    # 先拉取
    local_mapping = pull_from_feishu(local_mapping)
    
    # 再推送
    local_mapping = push_to_feishu(local_mapping)
    
    # 保存
    save_local_mapping(local_mapping)
    
    print(f"\n🎉 双向同步完成！共 {len(local_mapping)} 个空间/容器")


def main():
    parser = argparse.ArgumentParser(description="空间表双向同步")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--push", action="store_true", help="本地推送到飞书")
    group.add_argument("--pull", action="store_true", help="从飞书拉取到本地")
    group.add_argument("--sync", action="store_true", help="双向同步")
    group.add_argument("--init", action="store_true", help="从 space_map.json 初始化映射")
    
    args = parser.parse_args()
    
    if args.sync:
        sync()
    elif args.pull:
        local_mapping = load_local_mapping()
        if not local_mapping:
            local_mapping = flatten_space_map()
        local_mapping = pull_from_feishu(local_mapping)
        save_local_mapping(local_mapping)
    elif args.push:
        local_mapping = load_local_mapping()
        if not local_mapping:
            local_mapping = flatten_space_map()
        local_mapping = push_to_feishu(local_mapping)
        save_local_mapping(local_mapping)
    elif args.init:
        local_mapping = flatten_space_map()
        save_local_mapping(local_mapping)


if __name__ == "__main__":
    main()
