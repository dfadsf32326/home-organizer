#!/usr/bin/env python3
import json
import subprocess
import os
import time

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"

SPACE_TABLE_ID = "tbl2cA30WNdkjsLS"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SPACE_TREE_FILE = os.path.join(PROJECT_ROOT, "data", "space_tree.json")
FIELD_MAPPING_FILE = os.path.join(PROJECT_ROOT, "data", "field_mapping.json")

def load_field_mapping():
    with open(FIELD_MAPPING_FILE, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    fields = mapping.get('tables', {}).get('spaces', {}).get('fields', {})
    
    # 构建双向映射
    key_to_fld = {k: v['feishu_id'] for k, v in fields.items()}
    fld_to_key = {v['feishu_id']: k for k, v in fields.items()}
    return key_to_fld, fld_to_key

def extract_link_id(val):
    """提取关联字段的 record_id"""
    if not val: return None
    if isinstance(val, list) and len(val) > 0:
        if isinstance(val[0], dict):
            return val[0].get("id") or val[0].get("record_id")
        return val[0]
    return None

def normalize_select(val):
    """归一化单选/多选字段值为字符串"""
    if isinstance(val, list):
        return val[0] if val else None
    return val

def wrap_select(val):
    """将字符串包装为飞书单选/多选所需的列表格式"""
    if val is None: return None
    return [val] if isinstance(val, str) else val

def is_content_equal(local, remote):
    """比对本地与云端内容是否一致"""
    checks = [
        (local.get("name"), remote.get("name")),
        (local.get("type"), normalize_select(remote.get("type"))),
        (local.get("notes"), remote.get("notes")),
        (local.get("frequency"), normalize_select(remote.get("frequency"))),
        (local.get("status"), normalize_select(remote.get("status"))),
        (local.get("primary_activity"), remote.get("primary_activity")),
        # 注意: 这里暂不深度比对 parent_id, 因为牵扯到 record_id 和 local_id 的转换
        # 只比对节点自身属性
    ]
    
    for l_val, r_val in checks:
        l_norm = l_val if l_val is not None else ""
        r_norm = r_val if r_val is not None else ""
        if str(l_norm).strip() != str(r_norm).strip():
            return False
    return True

def main():
    print("加载字段映射配置...")
    key_to_fld, fld_to_key = load_field_mapping()
    
    print("1. 拉取飞书最新空间数据...")
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
    
    # 格式化云端数据为字典: record_id -> 节点数据
    remote_nodes = {}
    rid_to_local_id = {} # record_id -> 本地 id 的映射
    feishu_name_to_rid = {} # 名字 -> record_id 的映射，处理重复或匹配用
    
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
                        
        if node.get("id"):
            rid_to_local_id[rid] = node["id"]
        if node.get("name"):
            feishu_name_to_rid[node["name"]] = rid
            
        remote_nodes[rid] = node

    # 转换云端数据的 parent_rid 为 本地的 parent_id
    for rid, node in remote_nodes.items():
        parent_rid = node.pop("parent_rid", None)
        if parent_rid and parent_rid in rid_to_local_id:
            node["parent_id"] = rid_to_local_id[parent_rid]
            
    print(f"  ✅ 成功获取云端记录数: {len(remote_nodes)}")

    print("\n2. 读取本地 space_tree.json...")
    with open(SPACE_TREE_FILE, 'r', encoding='utf-8') as f:
        local_data = json.load(f)
    local_nodes = local_data.get("nodes", [])
    
    # 构建本地索引
    local_nodes_map = {n.get("id"): n for n in local_nodes if n.get("id")}
    
    push_count = 0
    pull_count = 0
    skip_count = 0
    new_local_count = 0
    processed_remote_rids = set()

    print("\n3. 交叉比对，执行双向同步...")
    
    # 阶段 A：以本地为基准，向飞书同步（推）或从飞书更新（拉）
    for local_node in local_nodes:
        lid = local_node.get("id")
        rid = local_node.get("record_id")
        name = local_node.get("name")
        
        if not lid or not name: continue
        
        remote = remote_nodes.get(rid)
        
        # 如果 record_id 没对上，尝试用 name 匹配飞书记录
        if not remote and name in feishu_name_to_rid:
            rid = feishu_name_to_rid[name]
            remote = remote_nodes.get(rid)
            local_node["record_id"] = rid
            
        if remote:
            processed_remote_rids.add(rid)
            
            if is_content_equal(local_node, remote):
                # 简单处理 parent_id 比对，如果父节点也不变则跳过
                if local_node.get("parent_id") == remote.get("parent_id"):
                    skip_count += 1
                    continue
                
            # 这里简单起见，空间表的双向同步我们让飞书优先覆盖本地
            # 如果本地有改动想推上云，需要时间戳或者单独推送指令，这里默认拉取覆盖
            print(f"  ↓ 拉取更新: {name}")
            local_node["name"] = remote.get("name") or local_node.get("name")
            local_node["type"] = remote.get("type") or local_node.get("type", "未分类")
            local_node["notes"] = remote.get("notes") or local_node.get("notes")
            local_node["frequency"] = remote.get("frequency") or local_node.get("frequency")
            local_node["status"] = remote.get("status") or local_node.get("status")
            local_node["primary_activity"] = remote.get("primary_activity") or local_node.get("primary_activity")
            local_node["parent_id"] = remote.get("parent_id") or local_node.get("parent_id")
            pull_count += 1
            
        else:
            # 云端不存在，说明是本地新建的，推送到飞书
            print(f"  ↑ 推送新建: {name}")
            fields_to_update = {
                key_to_fld["name"]: name,
                key_to_fld["type"]: wrap_select(local_node.get("type", "未分类")),
                key_to_fld["id"]: lid
            }
            if local_node.get("notes"): fields_to_update[key_to_fld["notes"]] = local_node.get("notes")
            if local_node.get("frequency"): fields_to_update[key_to_fld["frequency"]] = wrap_select(local_node.get("frequency"))
            if local_node.get("status"): fields_to_update[key_to_fld["status"]] = wrap_select(local_node.get("status"))
            if local_node.get("primary_activity"): fields_to_update[key_to_fld["primary_activity"]] = local_node.get("primary_activity")
            
            cmd = [LARK_CLI, "base", "+record-upsert", "--base-token", BASE_TOKEN, "--table-id", SPACE_TABLE_ID, "--json", json.dumps(fields_to_update, ensure_ascii=False)]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                try:
                    rj = json.loads(res.stdout)
                    new_rid = (rj.get("data", {}).get("record_id_list") or [None])[0] or rj.get("data", {}).get("record", {}).get("record_id")
                    if new_rid:
                        local_node["record_id"] = new_rid
                        rid_to_local_id[new_rid] = lid # 给等会儿建父子关系用
                        feishu_name_to_rid[name] = new_rid
                        push_count += 1
                except: pass

    # 阶段 B：以飞书为基准，拉取云端新增的空间到本地
    for rid, remote in remote_nodes.items():
        if rid in processed_remote_rids:
            continue
            
        print(f"  ★ 发现云端新空间: {remote.get('name')}")
        # 如果飞书上没写空间ID，使用记录名兜底
        new_lid = remote.get("id") or f"space_{rid[-6:]}"
        
        new_node = {
            "id": new_lid,
            "record_id": rid,
            "name": remote.get("name"),
            "type": remote.get("type", "未分类"),
            "notes": remote.get("notes"),
            "frequency": remote.get("frequency"),
            "status": remote.get("status"),
            "primary_activity": remote.get("primary_activity"),
            "parent_id": remote.get("parent_id")
        }
        
        # 清除掉为 None 的键
        new_node = {k: v for k, v in new_node.items() if v is not None}
        
        local_nodes.append(new_node)
        rid_to_local_id[rid] = new_lid
        new_local_count += 1
        
        # 反向更新云端的空间 ID (如果云端漏填了)
        if not remote.get("id"):
            subprocess.run([LARK_CLI, "base", "+record-upsert", "--base-token", BASE_TOKEN, "--table-id", SPACE_TABLE_ID, "--record-id", rid, "--json", json.dumps({key_to_fld["id"]: new_lid}, ensure_ascii=False)])

    print("\n4. 同步父子层级关系(推送到飞书)...")
    # 因为父子关系是由 parent_id 和 record_id 决定的，双向同步后需要确保飞书的关联字段是对的
    # 此处统一以本地整理后的 parent_id 向飞书推送一波关联关系（增量覆盖）
    id_to_rid = {n["id"]: n.get("record_id") for n in local_nodes if n.get("id") and n.get("record_id")}
    
    for node in local_nodes:
        parent_id = node.get("parent_id")
        rid = node.get("record_id")
        if not parent_id or not rid: continue
        
        parent_rid = id_to_rid.get(parent_id)
        
        # 检查飞书上该记录原本的 parent_id 是否已经对了
        remote = remote_nodes.get(rid)
        if remote and remote.get("parent_id") == parent_id:
            continue # 没变，跳过
            
        if parent_rid:
            link_fields = {key_to_fld["parent_id"]: [parent_rid]}
            cmd = [LARK_CLI, "base", "+record-upsert", "--base-token", BASE_TOKEN, "--table-id", SPACE_TABLE_ID, "--record-id", rid, "--json", json.dumps(link_fields, ensure_ascii=False)]
            subprocess.run(cmd, capture_output=True)
            print(f"  🔗 更新飞书层级: {node['name']} -> 父级 {parent_id}")
            time.sleep(0.05)
            
    print("\n5. 保存双向同步后的本地文件...")
    # 按从父到子的粗略顺序排序
    local_nodes.sort(key=lambda x: (x.get('parent_id') is not None, x.get('type', '')))
    
    local_data["nodes"] = local_nodes
    with open(SPACE_TREE_FILE, 'w', encoding='utf-8') as f:
        json.dump(local_data, f, ensure_ascii=False, indent=2)
        
    print(f"🎉 同步完成！推送新建 {push_count}，拉取更新 {pull_count}，发现云端新增 {new_local_count}，无变化跳过 {skip_count}。")

if __name__ == '__main__':
    main()
