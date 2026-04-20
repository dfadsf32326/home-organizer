import json
import subprocess
import os
import uuid
from datetime import datetime

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
TABLE_ID = "tbluMVXBpHIJDGyi"
PROJECT_ROOT = "/Users/robinlu/Self-established_skill/home-organizer"
ITEMS_FILE = os.path.join(PROJECT_ROOT, "data/items.json")

def parse_time(t_str):
    if not t_str: return 0
    try:
        if isinstance(t_str, (int, float)): return float(t_str) / 1000.0
        return datetime.fromisoformat(t_str.replace('Z', '+00:00')).timestamp()
    except: return 0

def get_feishu_records():
    cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--limit", "500"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0: return {}
    
    remote_data = {}
    try:
        data_full = json.loads(res.stdout)
        data = data_full.get("data", {})
        records = data.get("data", [])
        field_names = data.get("fields", [])
        record_ids = data.get("record_id_list", [])
        
        idx_map = {name: i for i, name in enumerate(field_names)}
        
        for i, row in enumerate(records):
            rid = record_ids[i]
            lid = row[idx_map["本地数据库ID"]] if "本地数据库ID" in idx_map and idx_map["本地数据库ID"] < len(row) else None
            
            item_info = {
                "record_id": rid,
                "local_id": lid,
                "name": row[idx_map["物品名称"]] if "物品名称" in idx_map else None,
                "category": row[idx_map["大类"]] if "大类" in idx_map else None,
                "sub_category": row[idx_map["子分类"]] if "子分类" in idx_map else None,
                "location": row[idx_map["位置"]] if "位置" in idx_map else None,
                "container": row[idx_map["容器"]] if "容器" in idx_map else None,
                "updated_at": row[idx_map["更新时间"]] if "更新时间" in idx_map else None,
                "status": row[idx_map["状态"]] if "状态" in idx_map else None
            }
            remote_data[rid] = item_info
    except: pass
    return remote_data

def sync():
    if not os.path.exists(ITEMS_FILE): return

    with open(ITEMS_FILE, 'r', encoding='utf-8') as f:
        items_data = json.load(f)
    
    local_items = items_data.get("items", [])
    remote_data = get_feishu_records()
    
    # 防止重复录入
    local_by_rid = {it.get("feishu_record_id"): it for it in local_items if it.get("feishu_record_id")}
    local_by_lid = {it.get("id"): it for it in local_items if it.get("id")}
    
    processed_remote_rids = set()
    push_count = 0
    pull_count = 0
    new_local_count = 0

    # 第一阶段：处理本地项
    for item in local_items:
        lid = item.get("id")
        rid = item.get("feishu_record_id")
        
        remote = remote_data.get(rid) or remote_data.get(lid)
        
        if remote:
            rid = remote["record_id"]
            item["feishu_record_id"] = rid
            processed_remote_rids.add(rid)
            
            local_ts = parse_time(item.get("updated_at"))
            remote_ts = parse_time(remote["updated_at"])
            
            # 云端更晚 -> 拉取
            if remote_ts > local_ts + 5:
                print(f"↓ 拉取更新: {item.get('name')}")
                item["location"] = remote["location"] or item["location"]
                item["container"] = remote["container"] or item["container"]
                if isinstance(remote["category"], list) and remote["category"]:
                    item["category"] = remote["category"][0]
                item["updated_at"] = datetime.fromtimestamp(remote_ts).isoformat()
                pull_count += 1
                continue
        
        # 否则 -> 推送
        fields = {
            "物品名称": item.get("name"),
            "大类": [item.get("category")] if item.get("category") else [],
            "子分类": item.get("sub_category"),
            "位置": item.get("location"),
            "容器": item.get("container"),
            "本地数据库ID": lid
        }
        # 只有当本地有状态且合法时才推状态
        if item.get("status"):
            fields["状态"] = [item["status"]] if isinstance(item["status"], str) else item["status"]

        cmd = [LARK_CLI, "base", "+record-upsert", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--json", json.dumps(fields, ensure_ascii=False)]
        if rid: cmd.extend(["--record-id", rid])
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            push_count += 1
            try:
                rj = json.loads(res.stdout)
                new_rid = (rj.get("data", {}).get("record", {}).get("record_id_list") or [None])[0]
                if new_rid:
                    item["feishu_record_id"] = new_rid
                    processed_remote_rids.add(new_rid)
            except: pass
        else:
            print(f"Sync failed for {item.get('name')}: {res.stderr}")

    # 第二阶段：反向录入
    for rid, remote in remote_data.items():
        if rid in processed_remote_rids: continue
        
        print(f"★ 发现云端新物品: {remote['name']}")
        new_lid = remote["local_id"] or f"item-lark-{uuid.uuid4().hex[:8]}"
        if not remote["local_id"]:
            subprocess.run([LARK_CLI, "base", "+record-update", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--record-id", rid, "--json", json.dumps({"本地数据库ID": new_lid}, ensure_ascii=False)])
        
        new_item = {
            "id": new_lid,
            "name": remote["name"],
            "category": remote["category"][0] if isinstance(remote["category"], list) and remote["category"] else remote["category"],
            "sub_category": remote["sub_category"],
            "location": remote["location"],
            "container": remote["container"],
            "status": remote["status"][0] if isinstance(remote["status"], list) and remote["status"] else remote["status"],
            "updated_at": datetime.now().isoformat(),
            "feishu_record_id": rid
        }
        local_items.append(new_item)
        new_local_count += 1

    # 去重清理：如果本地有重复的 ID（比如刚才测试产生的）
    unique_items = []
    seen_ids = set()
    for it in local_items:
        if it["id"] not in seen_ids:
            unique_items.append(it)
            seen_ids.add(it["id"])
    items_data["items"] = unique_items

    with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(items_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 同步完成！推送 {push_count}，拉取 {pull_count}，新增录入 {new_local_count}。")

if __name__ == "__main__":
    sync()
