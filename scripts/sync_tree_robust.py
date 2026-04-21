#!/usr/bin/env python3
import json
import subprocess
import os

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
SPACE_TABLE_ID = "tbl2cA30WNdkjsLS"
PROJECT_ROOT = "/Users/robinlu/Self-established_skill/home-organizer"
SPACE_TREE_FILE = os.path.join(PROJECT_ROOT, "data", "space_tree.json")

TYPE_MAP = {
    "room": "房间",
    "area": "区域",
    "surface": "表面/台面",
    "furniture": "家具",
    "cabinet": "柜子",
    "container": "容器",
    "sub_area": "内部分区",
    "appliance": "电器",
    "wall": "墙面",
    "wall_hook": "墙上挂钩",
    "organizer": "收纳工具",
    "unspecified": "未分类"
}

def main():
    print("1. 拉取飞书现有数据并清理重复的脏数据...")
    cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", SPACE_TABLE_ID, "--limit", "500"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    feishu_records = {} # name -> rid
    
    if res.returncode == 0:
        data = json.loads(res.stdout).get("data", {})
        records = data.get("data", [])
        fields = data.get("fields", [])
        record_ids = data.get("record_id_list", [])
        
        if "容器名" in fields:
            name_idx = fields.index("容器名")
            for i, row in enumerate(records):
                name = row[name_idx]
                if isinstance(name, list): name = name[0]
                rid = record_ids[i]
                
                if name in feishu_records:
                    print(f"  🗑️ 删除重复数据: {name} ({rid})")
                    subprocess.run([LARK_CLI, "base", "+record-delete", "--base-token", BASE_TOKEN, "--table-id", SPACE_TABLE_ID, "--yes", "--record-id", rid], capture_output=True)
                elif name:
                    feishu_records[name] = rid
                    
    print(f"  ✅ 现存唯一有效记录数: {len(feishu_records)}")
    
    print("\n2. 读取本地 space_tree.json...")
    with open(SPACE_TREE_FILE, 'r', encoding='utf-8') as f:
        local_data = json.load(f)
    nodes = local_data.get("nodes", [])
    
    print("\n3. 同步节点(含中文类型)并回写 record_id...")
    for node in nodes:
        name = node.get("name")
        if not name: continue
        
        zh_type = TYPE_MAP.get(node.get("type", "unspecified"), "未分类")
        fields_to_update = {
            "容器名": name,
            "类型": zh_type
        }
        if node.get("notes"):
            fields_to_update["备注"] = node.get("notes")
            
        rid = feishu_records.get(name)
        
        if rid:
            # Update existing
            cmd = [LARK_CLI, "base", "+record-upsert", "--base-token", BASE_TOKEN, "--table-id", SPACE_TABLE_ID, "--record-id", rid, "--json", json.dumps(fields_to_update, ensure_ascii=False)]
            subprocess.run(cmd, capture_output=True)
            node["record_id"] = rid
            print(f"  🔄 更新并回写: {name} ({rid})")
        else:
            # Create new
            cmd = [LARK_CLI, "base", "+record-upsert", "--base-token", BASE_TOKEN, "--table-id", SPACE_TABLE_ID, "--json", json.dumps(fields_to_update, ensure_ascii=False)]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                rj = json.loads(res.stdout)
                new_rid = rj.get("data", {}).get("record", {}).get("record_id")
                if not new_rid:
                    new_rid = (rj.get("data", {}).get("record_id_list") or [None])[0]
                if new_rid:
                    node["record_id"] = new_rid
                    feishu_records[name] = new_rid
                    print(f"  ➕ 创建并回写: {name} ({new_rid})")
            else:
                print(f"  ❌ 创建失败: {name}")
                
    print("\n4. 建立父子关联关系...")
    # Build id -> rid map using the local ids
    id_to_rid = {n["id"]: n.get("record_id") for n in nodes if n.get("id") and n.get("record_id")}
    
    for node in nodes:
        parent_id = node.get("parent_id")
        rid = node.get("record_id")
        if not parent_id or not rid: continue
        
        parent_rid = id_to_rid.get(parent_id)
        if parent_rid:
            link_fields = {"父记录 2": [parent_rid]}
            cmd = [LARK_CLI, "base", "+record-upsert", "--base-token", BASE_TOKEN, "--table-id", SPACE_TABLE_ID, "--record-id", rid, "--json", json.dumps(link_fields, ensure_ascii=False)]
            subprocess.run(cmd, capture_output=True)
            print(f"  🔗 关联: {node['name']} -> 父级 ID {parent_id}")
            
    print("\n5. 保存带有 record_id 的本地文件...")
    with open(SPACE_TREE_FILE, 'w', encoding='utf-8') as f:
        json.dump(local_data, f, ensure_ascii=False, indent=2)
        
    print("🎉 全部完成！脏数据已清，层级已建，record_id 已回写。")

if __name__ == '__main__':
    main()
