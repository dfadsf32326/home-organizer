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

def push_records():
    with open(SPACE_TREE_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    nodes = data.get("nodes", [])
    
    print("\n📤 正在创建记录（包含类型和备注）...")
    name_to_record_id = {}
    
    for node in nodes:
        name = node.get("name")
        if not name: continue
        
        # 转换类型为中文
        raw_type = node.get("type", "unspecified")
        zh_type = TYPE_MAP.get(raw_type, raw_type)
        
        fields = {
            "容器名": name,
            "类型": zh_type
        }
        if node.get("notes"):
            fields["备注"] = node.get("notes")
            
        cmd = [LARK_CLI, "base", "+record-upsert", "--base-token", BASE_TOKEN, "--table-id", SPACE_TABLE_ID, "--json", json.dumps(fields, ensure_ascii=False)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            rj = json.loads(res.stdout)
            res_data = rj.get("data", {})
            
            # 由于使用的是upsert，返回值可能包含多个record_id，如果是创建的取第一个，如果是更新的取record里面的
            record_list = res_data.get("record_id_list", [])
            if record_list:
                rid = record_list[0]
            else:
                rid = res_data.get("record", {}).get("record_id")

            if rid:
                name_to_record_id[name] = rid
                print(f"  ✅ 创建成功: {name} ({zh_type}) rid: {rid}")
        else:
            print(f"❌ 创建失败 {name}: {res.stderr.strip()}")
            
    print(f"✅ 记录创建完成，共 {len(name_to_record_id)} 条。")
    return name_to_record_id, nodes

def link_records(name_to_record_id, nodes):
    print("\n🔗 正在重建父子关系...")
    name_to_parent_id = {n["name"]: n.get("parent_id") for n in nodes if n.get("name")}
    id_to_name = {n["id"]: n["name"] for n in nodes if n.get("id")}
    
    linked = 0
    for name, rid in name_to_record_id.items():
        parent_id = name_to_parent_id.get(name)
        if not parent_id: continue
        
        parent_name = id_to_name.get(parent_id)
        if not parent_name: continue
        
        parent_rid = name_to_record_id.get(parent_name)
        if parent_rid:
            fields = {"父记录 2": [parent_rid]}
            cmd = [LARK_CLI, "base", "+record-upsert", "--base-token", BASE_TOKEN, "--table-id", SPACE_TABLE_ID, "--record-id", rid, "--json", json.dumps(fields, ensure_ascii=False)]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                linked += 1
                print(f"  🔗 关联: {name} -> {parent_name}")
            else:
                print(f"  ❌ 关联失败 {name}: {res.stderr.strip()}")
                
    print(f"✅ 关系关联完成，共链接 {linked} 条记录。")

if __name__ == '__main__':
    name_to_rid, nodes = push_records()
    link_records(name_to_rid, nodes)
