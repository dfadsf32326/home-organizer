#!/usr/bin/env python3
"""
分类表双向同步脚本

功能：
1. 本地 → 飞书：将 category_mapping.json 中的分类推送到飞书分类表
2. 飞书 → 本地：从飞书分类表拉取数据更新 category_mapping.json

使用方式：
  python sync_category_mapping.py --push    # 本地推送飞书
  python sync_category_mapping.py --pull    # 飞书拉取本地
  python sync_category_mapping.py --sync    # 双向同步（先pull再push）
"""

import json
import subprocess
import os
import argparse
from datetime import datetime

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
CATEGORY_TABLE_ID = "tbl6Ew6fmmhqeeSP"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MAPPING_FILE = os.path.join(PROJECT_ROOT, "data", "category_mapping.json")
FIELD_MAPPING_FILE = os.path.join(PROJECT_ROOT, "data", "field_mapping.json")


def load_field_mapping():
    """加载字段映射配置（本地字段名 -> 飞书字段名/字段ID）"""
    if not os.path.exists(FIELD_MAPPING_FILE):
        print(f"⚠️  {FIELD_MAPPING_FILE} 不存在，请检查配置文件")
        return {}
    with open(FIELD_MAPPING_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_field_id(mapping, table_key, field_key):
    """从映射配置中获取指定表的字段 ID"""
    try:
        return mapping["tables"][table_key]["fields"][field_key]["feishu_id"]
    except (KeyError, TypeError):
        print(f"⚠️  未找到字段映射: {table_key}.{field_key}")
        return None


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


def get_feishu_categories():
    """从飞书分类表获取所有分类记录"""
    cmd = [LARK_CLI, "base", "+record-list", 
           "--base-token", BASE_TOKEN, 
           "--table-id", CATEGORY_TABLE_ID, 
           "--limit", "500"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    if res.returncode != 0:
        print(f"❌ 拉取飞书分类表失败: {res.stderr}")
        return {}
    
    # 加载字段映射配置
    fm = load_field_mapping()
    F = lambda key: get_field_id(fm, "categories", key)

    remote_data = {}
    try:
        data_full = json.loads(res.stdout)
        data = data_full.get("data", {})
        records = data.get("data", [])
        field_ids = data.get("field_id_list", [])
        record_ids = data.get("record_id_list", [])
        
        # 使用字段 ID 建立索引映射，避免字段重命名导致同步失败
        idx_map = {fid: i for i, fid in enumerate(field_ids)}
        
        for i, row in enumerate(records):
            rid = record_ids[i]
            
            def get_val(field_key):
                fid = F(field_key)
                if not fid:
                    return None
                idx = idx_map.get(fid)
                if idx is not None and idx < len(row):
                    return row[idx]
                return None
            
            # 子类名称可能是公式字段，按优先级尝试多个字段
            sub_name = get_val("sub_name") or get_val("cat_key") or get_val("sub_class")
            major = get_val("major")
            
            if sub_name:
                # 处理飞书返回的列表格式
                if isinstance(sub_name, list):
                    sub_name = sub_name[0] if sub_name else None
                if isinstance(major, list):
                    major = major[0] if major else None
                
                remote_data[sub_name] = {
                    "record_id": rid,
                    "major": major or ""
                }
    except Exception as e:
        print(f"❌ 解析飞书数据出错: {e}")
    
    return remote_data


def push_to_feishu(local_mapping):
    """将本地映射推送到飞书"""
    print("\n📤 推送本地分类到飞书...")

    # 加载字段映射配置
    fm = load_field_mapping()
    F = lambda key: get_field_id(fm, "categories", key)

    remote_data = get_feishu_categories()
    created = 0
    updated = 0

    for sub_name, info in local_mapping.items():
        record_id = info.get("record_id")
        major = info.get("major", "")

        # 检查飞书是否已存在
        if sub_name in remote_data:
            # 已存在，检查是否需要更新
            existing = remote_data[sub_name]
            if existing.get("record_id") and not record_id:
                # 本地缺少 record_id，补上
                local_mapping[sub_name]["record_id"] = existing["record_id"]
                print(f"  📝 补充 record_id: {sub_name}")
            continue

        # 不存在，创建新记录（使用字段 ID 推送）
        fields = {
            F("sub_class"): [sub_name],
            F("cat_key"):   sub_name,
            F("major"):     [major] if major else []
        }
        
        cmd = [LARK_CLI, "base", "+record-upsert",
               "--base-token", BASE_TOKEN,
               "--table-id", CATEGORY_TABLE_ID,
               "--json", json.dumps(fields, ensure_ascii=False)]
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            try:
                rj = json.loads(res.stdout)
                res_data = rj.get("data", {})
                new_rid = (res_data.get("record_id_list") or [None])[0] or \
                          res_data.get("record", {}).get("record_id")
                if new_rid:
                    local_mapping[sub_name]["record_id"] = new_rid
                    created += 1
                    print(f"  ✅ 创建: {sub_name} → {new_rid}")
            except:
                print(f"  ⚠️  创建成功但未返回 ID: {sub_name}")
        else:
            print(f"  ❌ 创建失败 {sub_name}: {res.stderr[:100]}")
    
    print(f"\n📊 推送完成：新建 {created} 条")
    return local_mapping


def pull_from_feishu(local_mapping):
    """从飞书拉取分类更新本地"""
    print("\n📥 从飞书拉取分类到本地...")
    
    remote_data = get_feishu_categories()
    
    added = 0
    updated = 0
    
    for sub_name, info in remote_data.items():
        record_id = info.get("record_id")
        major = info.get("major", "")
        
        if sub_name not in local_mapping:
            # 本地不存在，新增
            local_mapping[sub_name] = {
                "record_id": record_id,
                "major": major
            }
            added += 1
            print(f"  ➕ 新增: {sub_name} ({major})")
        else:
            # 本地已存在，更新 record_id（如果本地缺失或不同）
            local_record_id = local_mapping[sub_name].get("record_id")
            if record_id and local_record_id != record_id:
                local_mapping[sub_name]["record_id"] = record_id
                updated += 1
                print(f"  🔄 更新 ID: {sub_name}")
            
            # 更新 major（如果本地缺失）
            if major and not local_mapping[sub_name].get("major"):
                local_mapping[sub_name]["major"] = major
    
    print(f"\n📊 拉取完成：新增 {added} 条，更新 {updated} 条")
    return local_mapping


def sync():
    """双向同步：先拉取再推送"""
    local_mapping = load_local_mapping()
    
    # 先拉取（获取飞书端的更新和新分类）
    local_mapping = pull_from_feishu(local_mapping)
    
    # 再推送（将本地独有的分类推送到飞书）
    local_mapping = push_to_feishu(local_mapping)
    
    # 保存
    save_local_mapping(local_mapping)
    
    print(f"\n🎉 双向同步完成！共 {len(local_mapping)} 个分类")


def main():
    parser = argparse.ArgumentParser(description="分类表双向同步")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--push", action="store_true", help="本地推送到飞书")
    group.add_argument("--pull", action="store_true", help="从飞书拉取到本地")
    group.add_argument("--sync", action="store_true", help="双向同步")
    
    args = parser.parse_args()
    
    if args.sync:
        sync()
    elif args.pull:
        local_mapping = load_local_mapping()
        local_mapping = pull_from_feishu(local_mapping)
        save_local_mapping(local_mapping)
    elif args.push:
        local_mapping = load_local_mapping()
        local_mapping = push_to_feishu(local_mapping)
        save_local_mapping(local_mapping)


if __name__ == "__main__":
    main()
