#!/usr/bin/env python3
"""
从飞书拉取分类表到本地 category_mapping.json
用法: python3 scripts/sync_categories.py
"""
import json
import subprocess
import os

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# 分类表配置 (从 field_mapping.json 读取)
FIELD_MAPPING_FILE = os.path.join(PROJECT_ROOT, "data/field_mapping.json")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "data/category_mapping.json")

def load_field_mapping():
    with open(FIELD_MAPPING_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_field_id(mapping, field_key):
    """获取分类表字段ID"""
    try:
        return mapping["tables"]["categories"]["fields"][field_key]["feishu_id"]
    except:
        return None

def fetch_categories(table_id):
    """从飞书拉取分类表数据"""
    all_records = []
    all_field_ids = []
    all_record_ids = []
    offset = 0
    page_size = 200
    
    while True:
        cmd = [
            LARK_CLI, "base", "+record-list",
            "--base-token", BASE_TOKEN,
            "--table-id", table_id,
            "--limit", str(page_size),
            "--offset", str(offset)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        
        if res.returncode != 0:
            print(f"❌ 从飞书拉取分类表失败！")
            print(res.stderr)
            return None, None, None
        
        try:
            data_full = json.loads(res.stdout)
            data = data_full.get("data", {})
            records = data.get("data", [])
            field_ids = data.get("field_id_list", [])
            record_ids = data.get("record_id_list", [])
            has_more = data.get("has_more", False)
            
            all_records.extend(records)
            all_field_ids = field_ids
            all_record_ids.extend(record_ids)
            
            print(f"  已拉取 {len(all_records)} 条分类记录...")
            
            if not has_more:
                break
            
            offset += len(records)
        except Exception as e:
            print(f"❌ 数据解析失败: {e}")
            return None, None, None
    
    return all_records, all_field_ids, all_record_ids

def build_mapping(records, field_ids, record_ids, field_mapping):
    """构建分类映射"""
    # 获取字段索引
    sub_class_fid = get_field_id(field_mapping, "sub_class")
    major_fid = get_field_id(field_mapping, "major")
    
    if not sub_class_fid or not major_fid:
        print("❌ 无法获取分类表字段ID")
        return {}
    
    try:
        sub_class_idx = field_ids.index(sub_class_fid)
        major_idx = field_ids.index(major_fid)
    except ValueError:
        print("❌ 字段ID不在field_id_list中")
        return {}
    
    mapping = {}
    for i, row in enumerate(records):
        rid = record_ids[i]
        sub_class_raw = row[sub_class_idx] if sub_class_idx < len(row) else None
        major_raw = row[major_idx] if major_idx < len(row) else None
        
        # sub_class 可能是列表或字符串
        if isinstance(sub_class_raw, list) and len(sub_class_raw) > 0:
            sub_class = sub_class_raw[0]
        else:
            sub_class = sub_class_raw
        
        # major 可能是列表或字符串
        if isinstance(major_raw, list) and len(major_raw) > 0:
            major_val = major_raw[0]
        else:
            major_val = major_raw
        
        if sub_class:
            mapping[sub_class] = {
                "record_id": rid,
                "major": major_val
            }
    
    return mapping

def main():
    print("↓ 正在从飞书拉取分类表...")
    
    # 加载字段映射
    field_mapping = load_field_mapping()
    table_id = field_mapping["tables"]["categories"]["table_id"]
    
    print(f"  分类表ID: {table_id}")
    
    # 拉取数据
    records, field_ids, record_ids = fetch_categories(table_id)
    
    if records is None:
        return
    
    # 构建映射
    mapping = build_mapping(records, field_ids, record_ids, field_mapping)
    
    # 保存到本地
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 分类表同步完成！共 {len(mapping)} 条分类已保存到 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()