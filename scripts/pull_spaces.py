#!/usr/bin/env python3
import json
import subprocess
import os

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN="PS56bPhyNaWXRdsJX78cxyIOnJb"
SPACE_TABLE_ID = "tbl2cA30WNdkjsLS"
PROJECT_ROOT = "/Users/robinlu/Self-established_skill/home-organizer"
SPACE_TREE_FILE = os.path.join(PROJECT_ROOT, "data", "space_tree.json")
FIELD_MAPPING_FILE = os.path.join(PROJECT_ROOT, "data", "field_mapping.json")

TYPE_MAP_REVERSE = {
    "房间": "room",
    "区域": "area",
    "表面/台面": "surface",
    "家具": "furniture",
    "柜子": "cabinet",
    "容器": "container",
    "内部分区": "sub_area",
    "电器": "appliance",
    "墙面": "wall",
    "墙上挂钩": "wall_hook",
    "收纳工具": "organizer",
    "未分类": "unspecified"
}

def load_field_mapping():
    with open(FIELD_MAPPING_FILE, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    fields = mapping.get('tables', {}).get('spaces', {}).get('fields', {})
    # 反向映射：feishu_field_id -> local_key
    return {v['feishu_id']: k for k, v in fields.items()}

def extract_link_id(val):
    if not val: return None
    if isinstance(val, list) and len(val) > 0:
        if isinstance(val[0], dict):
            return val[0].get("id") or val[0].get("record_id")
        return val[0]
    return None

def main():
    print("加载字段映射...")
    fld_to_key = load_field_mapping()

    print("拉取飞书空间树数据...")
    cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", SPACE_TABLE_ID, "--limit", "500"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"❌ 拉取失败: {res.stderr}")
        return

    data_full = json.loads(res.stdout)
    records = data_full.get("data", {}).get("data", [])
    field_ids = data_full.get("data", {}).get("field_id_list", [])
    record_ids = data_full.get("data", {}).get("record_id_list", [])

    idx_to_key = {i: fld_to_key[fid] for i, fid in enumerate(field_ids) if fid in fld_to_key}

    print(f"成功拉取到 {len(records)} 条记录，开始处理...")
    
    # 第一次遍历：提取所有节点基础信息并建立 record_id 到 local_id 的映射
    nodes = []
    rid_to_local_id = {}
    
    for i, row in enumerate(records):
        rid = record_ids[i]
        node = {"record_id": rid}
        
        for idx, val in enumerate(row):
            if idx in idx_to_key:
                key = idx_to_key[idx]
                if val is not None:
                    if key == "parent_id":
                        node["parent_rid"] = extract_link_id(val)
                    elif key == "type":
                        # 直接保存中文类型
                        zh_val = val[0] if isinstance(val, list) else val
                        node[key] = zh_val
                    elif isinstance(val, list):
                        node[key] = val[0]
                    else:
                        node[key] = val
        
        # 确保每个节点都有 id，如果是飞书新增的，生成一个
        if not node.get("id") and node.get("name"):
            print(f"⚠️ 节点 '{node['name']}' 没有本地 ID，这不应该发生，请确保所有飞书记录都有 '空间ID'。")
            continue
            
        if node.get("id"):
            rid_to_local_id[rid] = node["id"]
        
        nodes.append(node)

    # 第二次遍历：将 parent_rid 转换为本地的 parent_id
    for node in nodes:
        parent_rid = node.pop("parent_rid", None)
        if parent_rid and parent_rid in rid_to_local_id:
            node["parent_id"] = rid_to_local_id[parent_rid]
            
    # 按照先有 parent，再有 child 的粗略顺序排序（不是必须，但好看点）
    nodes.sort(key=lambda x: (x.get('parent_id') is not None, x.get('type', '')))

    print(f"准备覆写本地 space_tree.json，共计 {len(nodes)} 个节点...")
    tree_data = {"nodes": nodes}
    with open(SPACE_TREE_FILE, 'w', encoding='utf-8') as f:
        json.dump(tree_data, f, ensure_ascii=False, indent=2)

    print("🎉 同步到本地完成！")

if __name__ == '__main__':
    main()
