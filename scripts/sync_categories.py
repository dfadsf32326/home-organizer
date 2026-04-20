import json
import subprocess
import os
import re

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
CATEGORY_TABLE_ID = "tbl6Ew6fmmhqeeSP"
PROJECT_ROOT = "/Users/robinlu/Self-established_skill/home-organizer"
CLASSIFICATION_FILE = os.path.join(PROJECT_ROOT, "CLASSIFICATION_STANDARD.md")
MAPPING_FILE = os.path.join(PROJECT_ROOT, "data", "category_mapping.json")

def parse_markdown_categories():
    """解析 Markdown 字典获取完整的大类和子类映射"""
    if not os.path.exists(CLASSIFICATION_FILE):
        print(f"找不到分类文件: {CLASSIFICATION_FILE}")
        return {}

    categories = {}
    current_major = None
    
    with open(CLASSIFICATION_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # 解析大类 (例如: "### 1. 🍎 饮食供应 (Diet & Kitchen)")
            major_match = re.match(r'^###\s+\d+\.\s+([^()]+)', line)
            if major_match:
                current_major = major_match.group(1).strip()
                categories[current_major] = []
                continue
                
            # 解析子类 (例如: "*   `生鲜/冷藏食品` (肉、蛋、奶、生鲜水果)")
            sub_match = re.match(r'^\*\s+`([^`]+)`', line)
            if sub_match and current_major:
                sub_category = sub_match.group(1).strip()
                categories[current_major].append(sub_category)
                
    return categories

def get_feishu_categories():
    """从飞书多维表格获取现有的子类记录"""
    cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", CATEGORY_TABLE_ID, "--limit", "500"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"拉取飞书分类表失败: {res.stderr}")
        return {}
    
    remote_data = {}
    try:
        data_full = json.loads(res.stdout)
        data = data_full.get("data", {})
        records = data.get("data", [])
        field_names = data.get("fields", [])
        record_ids = data.get("record_id_list", [])
        
        idx_map = {name: i for i, name in enumerate(field_names)}
        
        # 字段大概是: "子类名称", "子类主键", "大类", "子类"
        for i, row in enumerate(records):
            rid = record_ids[i]
            
            def get_val(fname):
                idx = idx_map.get(fname)
                if idx is not None and idx < len(row):
                    return row[idx]
                return None

            sub_cat_name = get_val("子类名称")
            if sub_cat_name:
                remote_data[sub_cat_name] = {
                    "record_id": rid,
                    "major_category": get_val("大类"), # 可能是列表
                    "sub_category_primary": get_val("子类主键")
                }
    except Exception as e:
        print(f"解析飞书数据出错: {e}")
        
    return remote_data

def sync_and_build_mapping():
    """双向比对并建立缓存映射"""
    print("解析本地 Markdown 分类字典...")
    local_categories = parse_markdown_categories()
    
    print("拉取飞书云端分类表数据...")
    remote_categories = get_feishu_categories()
    
    mapping = {}
    new_records_created = 0
    
    # 遍历本地全量分类
    for major, subs in local_categories.items():
        for sub in subs:
            if sub in remote_categories:
                # 已存在，直接获取 record_id
                mapping[sub] = {
                    "record_id": remote_categories[sub]["record_id"],
                    "major": major
                }
            else:
                # 不存在，需要在飞书创建
                print(f"发现本地新子类 [{sub}] (属于 {major})，准备在飞书创建...")
                
                # 构建飞书需要的数据格式 (大类可能是单选/多选字段，如果是多选或链接需要传数组)
                fields = {
                    "子类名称": sub,
                    "大类": [major] if major else [],
                    "子类主键": sub, # 如果有这个字段
                    "子类": [sub] # 可能有些是自关联或需要这个字段
                }
                
                cmd = [
                    LARK_CLI, "base", "+record-upsert", 
                    "--base-token", BASE_TOKEN, 
                    "--table-id", CATEGORY_TABLE_ID, 
                    "--json", json.dumps(fields, ensure_ascii=False)
                ]
                
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0:
                    try:
                        rj = json.loads(res.stdout)
                        res_data = rj.get("data", {})
                        # 处理不同接口返回 ID 路径不一致的问题
                        new_rid = (res_data.get("record_id_list") or [None])[0] or res_data.get("record", {}).get("record_id")
                        
                        if new_rid:
                            mapping[sub] = {
                                "record_id": new_rid,
                                "major": major
                            }
                            new_records_created += 1
                            print(f"  ✅ 创建成功, Record ID: {new_rid}")
                        else:
                            print(f"  ❌ 创建成功但未返回 Record ID: {res.stdout}")
                    except Exception as e:
                        print(f"  ❌ 解析创建响应失败: {e}")
                else:
                    print(f"  ❌ 创建失败: {res.stderr}")
                    
    # 保存映射字典到本地
    os.makedirs(os.path.dirname(MAPPING_FILE), exist_ok=True)
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
        
    print(f"\n🎉 映射字典建立完成！总计 {len(mapping)} 个子类。")
    print(f"本次新创建 {new_records_created} 个分类记录。")
    print(f"字典已保存至: {MAPPING_FILE}")

if __name__ == "__main__":
    sync_and_build_mapping()
