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
    # 强制拉取更多字段以进行深度比对
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
            
            def get_val(fname):
                idx = idx_map.get(fname)
                if idx is not None and idx < len(row):
                    return row[idx]
                return None

            item_info = {
                "record_id": rid,
                "local_id": get_val("本地数据库ID"),
                "name": get_val("物品名称"),
                "category": get_val("大类"),
                "sub_category": get_val("子分类"),
                "location": get_val("位置"),
                "container": get_val("容器"),
                "updated_at": get_val("更新时间"),
                "status": get_val("状态"),
                "remark": get_val("备注")
            }
            remote_data[rid] = item_info
    except: pass
    return remote_data

def is_content_equal(local, remote):
    """
    深度比对本地物品内容和云端物品内容。
    """
    # 辅助函数处理飞书 Select 字段返回列表的问题
    def normalize_select(val):
        if isinstance(val, list):
            return val[0] if val else None
        return val

    checks = [
        (local.get("name"), remote.get("name")),
        (local.get("category"), normalize_select(remote.get("category"))),
        (local.get("sub_category"), remote.get("sub_category")),
        (local.get("location"), remote.get("location")),
        (local.get("container"), remote.get("container")),
        (local.get("status"), normalize_select(remote.get("status"))),
        (local.get("remark"), remote.get("remark"))
    ]
    
    for l_val, r_val in checks:
        # 统一处理 None 和空字符串，认为它们相等
        l_norm = l_val if l_val is not None else ""
        r_norm = r_val if r_val is not None else ""
        if str(l_norm).strip() != str(r_norm).strip():
            return False
    return True

def sync():
    if not os.path.exists(ITEMS_FILE): return

    with open(ITEMS_FILE, 'r', encoding='utf-8') as f:
        items_data = json.load(f)
    
    local_items = items_data.get("items", [])
    print("正在拉取云端数据进行比对...")
    remote_data = get_feishu_records()
    
    processed_remote_rids = set()
    push_count = 0
    pull_count = 0
    skip_count = 0
    new_local_count = 0

    # 第一阶段：双向同步现有项
    for item in local_items:
        lid = item.get("id")
        rid = item.get("feishu_record_id")
        
        # 匹配策略：优先 Record ID，其次本地 ID
        remote = remote_data.get(rid)
        if not remote:
            # 尝试通过本地数据库ID反向查找
            for r_rid, r_info in remote_data.items():
                if r_info["local_id"] == lid:
                    remote = r_info
                    rid = r_rid
                    item["feishu_record_id"] = rid
                    break
        
        if remote:
            processed_remote_rids.add(rid)
            local_ts = parse_time(item.get("updated_at"))
            remote_ts = parse_time(remote["updated_at"])
            
            # 核心逻辑：深度内容比对
            if is_content_equal(item, remote):
                # 内容完全一致，跳过 API 请求
                skip_count += 1
                continue
            
            # 内容不一致，判断谁更晚
            if remote_ts > local_ts + 2: # 2秒容差
                print(f"↓ 拉取更新: {item.get('name')}")
                item["name"] = remote["name"] or item["name"]
                item["location"] = remote["location"] or item["location"]
                item["container"] = remote["container"] or item["container"]
                item["sub_category"] = remote["sub_category"] or item.get("sub_category")
                item["remark"] = remote["remark"] or item.get("remark")
                
                def normalize_select(val):
                    return val[0] if isinstance(val, list) and val else val
                
                item["category"] = normalize_select(remote["category"]) or item.get("category")
                item["status"] = normalize_select(remote["status"]) or item.get("status")
                
                # 更新本地时间戳为云端时间
                item["updated_at"] = datetime.fromtimestamp(remote_ts).isoformat()
                pull_count += 1
                continue
            else:
                # 本地更新，准备推送
                pass
        
        # 推送逻辑
        fields = {
            "物品名称": item.get("name"),
            "大类": [item.get("category")] if item.get("category") else [],
            "子分类": item.get("sub_category"),
            "位置": item.get("location"),
            "容器": item.get("container"),
            "备注": item.get("remark"),
            "本地数据库ID": lid
        }
        if item.get("status"):
            fields["状态"] = [item["status"]] if isinstance(item["status"], str) else item["status"]

        cmd = [LARK_CLI, "base", "+record-upsert", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--json", json.dumps(fields, ensure_ascii=False)]
        if rid: cmd.extend(["--record-id", rid])
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            push_count += 1
            try:
                rj = json.loads(res.stdout)
                res_data = rj.get("data", {})
                # 处理不同接口返回 ID 路径不一致的问题
                new_rid = (res_data.get("record_id_list") or [None])[0] or res_data.get("record", {}).get("record_id")
                if new_rid:
                    item["feishu_record_id"] = new_rid
                    processed_remote_rids.add(new_rid)
            except: pass
        else:
            print(f"Sync failed for {item.get('name')}: {res.stderr}")

    # 第二阶段：反向录入云端新增
    for rid, remote in remote_data.items():
        if rid in processed_remote_rids: continue
        
        print(f"★ 发现云端新物品: {remote['name']}")
        new_lid = remote["local_id"] or f"item-lark-{uuid.uuid4().hex[:8]}"
        if not remote["local_id"]:
            subprocess.run([LARK_CLI, "base", "+record-update", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--record-id", rid, "--json", json.dumps({"本地数据库ID": new_lid}, ensure_ascii=False)])
        
        def normalize_select(val):
            return val[0] if isinstance(val, list) and val else val

        new_item = {
            "id": new_lid,
            "name": remote["name"],
            "category": normalize_select(remote["category"]),
            "sub_category": remote["sub_category"],
            "location": remote["location"],
            "container": remote["container"],
            "remark": remote["remark"],
            "status": normalize_select(remote["status"]) or "active",
            "updated_at": datetime.now().isoformat(),
            "feishu_record_id": rid
        }
        local_items.append(new_item)
        new_local_count += 1

    # 最终清理与保存
    unique_items = []
    seen_ids = set()
    for it in local_items:
        if it["id"] not in seen_ids:
            unique_items.append(it)
            seen_ids.add(it["id"])
    items_data["items"] = unique_items

    with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(items_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 同步完成！推送 {push_count}，拉取 {pull_count}，跳过内容未变项 {skip_count}，新增录入 {new_local_count}。")

if __name__ == "__main__":
    sync()
