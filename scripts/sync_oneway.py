import json
import subprocess
import os
import uuid
from datetime import datetime

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
TABLE_ID = "tbluMVXBpHIJDGyi"
CATEGORY_TABLE_ID = "tbl6Ew6fmmhqeeSP"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
ITEMS_FILE = os.path.join(DATA_DIR, "items.json")
MAPPING_FILE = os.path.join(DATA_DIR, "category_mapping.json")
FIELD_MAPPING_FILE = os.path.join(DATA_DIR, "field_mapping.json")

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def F(key):
    mapping = load_json(FIELD_MAPPING_FILE, {})
    return mapping.get("tables", {}).get("items", {}).get("fields", {}).get(key, {}).get("feishu_name", key)

def F_id(key):
    mapping = load_json(FIELD_MAPPING_FILE, {})
    return mapping.get("tables", {}).get("items", {}).get("fields", {}).get(key, {}).get("feishu_id")

def extract_link_record_id(field_data):
    if isinstance(field_data, list):
        return [item.get("id", "") for item in field_data if isinstance(item, dict)]
    elif isinstance(field_data, dict):
        return [field_data.get("id", "")]
    return []

def normalize_select(field_data):
    if isinstance(field_data, list) and len(field_data) > 0:
        return field_data[0]
    if isinstance(field_data, str):
        return field_data
    return None

def fetch_all_remote():
    cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--limit", "500"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("❌ 拉取失败:", res.stderr)
        return []
    
    try:
        rj = json.loads(res.stdout)
        return rj.get("data", {}).get("items", [])
    except Exception as e:
        print("❌ 解析失败:", e)
        return []

def parse_remote_record(r, mapping):
    fields = r.get("fields", {})
    rid = r.get("record_id")
    
    # 提取多维表格内部状态
    local_id = fields.get(F("local_id"))
    if not local_id:
        local_id = str(uuid.uuid4())
        
    remote_cat_rids = extract_link_record_id(fields.get(F("category_link")))
    cat_rid = remote_cat_rids[0] if remote_cat_rids else None
    
    remote_space_rids = extract_link_record_id(fields.get(F("space_record_id")))
    space_rid = remote_space_rids[0] if remote_space_rids else None
    
    sub_cat_name = fields.get(F("sub_category"))
    major_name = normalize_select(fields.get(F("major")))
    if cat_rid:
        for k, v in mapping.items():
            if v.get("record_id") == cat_rid:
                sub_cat_name = k
                major_name = v.get("major")
                break
                
    return {
        "id": local_id,
        "name": fields.get(F("name")),
        "category": major_name,
        "sub_category": sub_cat_name,
        "category_record_id": cat_rid,
        "space_record_id": space_rid,
        "location": fields.get(F("location_full")),
        "container": fields.get(F("container2")),
        "remark": fields.get(F("remark")),
        "status": normalize_select(fields.get(F("status"))) or "正常",
        "updated_at": datetime.now().isoformat(),
        "feishu_record_id": rid,
    }

def push_new_to_feishu(local_items):
    push_count = 0
    for item in local_items:
        if not item.get("feishu_record_id"):
            print(f"↑ 推送新物品至飞书: {item.get('name')}")
            fields = {
                F("name"):          item.get("name"),
                F("location_full"): item.get("location"),
                F("container2"):    item.get("container"),
                F("status"):        item.get("status") or "正常",
                F("remark"):        item.get("remark"),
                F("local_id"):      item.get("id"),
            }
            if item.get("category_record_id"):
                fields[F_id("category_link")] = [item.get("category_record_id")]
            if item.get("space_record_id"):
                fields[F_id("space_record_id")] = [item.get("space_record_id")]
                
            cmd = [LARK_CLI, "base", "+record-create", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--json", json.dumps(fields, ensure_ascii=False)]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                push_count += 1
            else:
                print(f"❌ 推送失败: {res.stderr}")
    return push_count

def sync():
    mapping = load_json(MAPPING_FILE, {})
    local_data = load_json(ITEMS_FILE, {"items": []})
    local_items = local_data.get("items", [])
    
    # 1. 扫描本地没有 feishu_record_id 的条目并单向 Push 到飞书
    push_count = push_new_to_feishu(local_items)
    
    # 2. 全量 Pull 飞书数据
    print("正在从飞书全量拉取数据作为唯一事实...")
    remote_records = fetch_all_remote()
    new_local_items = []
    
    for r in remote_records:
        parsed = parse_remote_record(r, mapping)
        new_local_items.append(parsed)
        
    local_data["items"] = new_local_items
    
    with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(local_data, f, ensure_ascii=False, indent=2)
        
    print(f"✅ 单向同步完成！新增推送 {push_count} 条，全量覆盖拉取 {len(new_local_items)} 条。")

if __name__ == "__main__":
    sync()
