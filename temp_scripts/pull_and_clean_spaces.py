import json
import subprocess
import os
import uuid

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
SPACE_TABLE_ID = "tbl2cA30WNdkjsLS"
FIELD_MAPPING_FILE = "data/field_mapping.json"
SPACE_TREE_FILE = "data/space_tree.json"
SPACE_MAP_FILE = "data/space_map.json"
SPACE_MAPPING_FILE = "data/space_mapping.json"

def load_field_mapping():
    with open(FIELD_MAPPING_FILE, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    fields = mapping.get('tables', {}).get('spaces', {}).get('fields', {})
    key_to_fld = {k: v['feishu_id'] for k, v in fields.items()}
    fld_to_key = {v['feishu_id']: k for k, v in fields.items()}
    return key_to_fld, fld_to_key

def extract_link_id(val):
    if not val: return None
    if isinstance(val, list) and len(val) > 0:
        if isinstance(val[0], dict):
            return val[0].get("id") or val[0].get("record_id")
        return val[0]
    return None

def normalize_select(val):
    if isinstance(val, list):
        return val[0] if val else None
    return val

def pull_spaces():
    print("1. 拉取飞书全量空间数据...")
    key_to_fld, fld_to_key = load_field_mapping()
    cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", SPACE_TABLE_ID, "--limit", "1000"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"❌ 拉取失败: {res.stderr}")
        return

    data_full = json.loads(res.stdout)
    records = data_full.get("data", {}).get("data", [])
    field_ids = data_full.get("data", {}).get("field_id_list", [])
    record_ids = data_full.get("data", {}).get("record_id_list", [])
    
    idx_to_key = {i: fld_to_key[fid] for i, fid in enumerate(field_ids) if fid in fld_to_key}
    
    remote_nodes = {}
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
                    elif key in ["type", "frequency", "status"]:
                        node[key] = normalize_select(val)
                    elif isinstance(val, list):
                        node[key] = val[0]
                    else:
                        node[key] = val
                        
        if not node.get("id"):
            node["id"] = "spc_" + str(uuid.uuid4())[:8]
            
        rid_to_local_id[rid] = node["id"]
        remote_nodes[rid] = node
        
    for rid, node in remote_nodes.items():
        parent_rid = node.pop("parent_rid", None)
        if parent_rid and parent_rid in rid_to_local_id:
            node["parent_id"] = rid_to_local_id[parent_rid]

    nodes_list = list(remote_nodes.values())
    
    # 2. 覆盖到 space_tree.json
    tree_data = {"version": "1.0", "last_sync": "0", "nodes": nodes_list}
    with open(SPACE_TREE_FILE, "w", encoding="utf-8") as f:
        json.dump(tree_data, f, ensure_ascii=False, indent=2)
    print(f"✅ 成功覆盖 space_tree.json，共保留 {len(nodes_list)} 个节点 (已清除云端删除的记录)。")

    # 3. 同步生成 space_map.json 和 space_mapping.json
    space_map = {}
    space_mapping = {}
    
    for node in nodes_list:
        name = node.get("name")
        rid = node.get("record_id")
        spc_id = node.get("id")
        
        if name and rid:
            space_map[name] = rid
            space_mapping[name] = {
                "record_id": rid,
                "local_id": spc_id,
                "type": node.get("type", "container")
            }
            
    with open(SPACE_MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(space_map, f, ensure_ascii=False, indent=2)
    print("✅ 成功更新 space_map.json")

    with open(SPACE_MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(space_mapping, f, ensure_ascii=False, indent=2)
    print("✅ 成功更新 space_mapping.json")

if __name__ == "__main__":
    pull_spaces()
