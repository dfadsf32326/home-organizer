import json
import subprocess
import os
from datetime import datetime

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
TABLE_ID = "tbluMVXBpHIJDGyi"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ITEMS_FILE = os.path.join(PROJECT_ROOT, "data/items.json")
MAPPING_FILE = os.path.join(PROJECT_ROOT, "data/category_mapping.json")
FIELD_MAPPING_FILE = os.path.join(PROJECT_ROOT, "data/field_mapping.json")

def load_field_mapping():
    if not os.path.exists(FIELD_MAPPING_FILE):
        return {}
    with open(FIELD_MAPPING_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_field_id(mapping, table_key, field_key):
    try:
        return mapping["tables"][table_key]["fields"][field_key]["feishu_id"]
    except:
        return None

def load_category_mapping():
    if not os.path.exists(MAPPING_FILE):
        return {}
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def normalize_select(val):
    if isinstance(val, list):
        return val[0] if val else None
    return val

def extract_link_record_id(link_val):
    if not link_val: return []
    if isinstance(link_val, list):
        ids = []
        for item in link_val:
            if isinstance(item, dict):
                ids.append(item.get("id") or item.get("record_id"))
            elif isinstance(item, str):
                ids.append(item)
        return [x for x in ids if x]
    return []

def get_feishu_records(F, mapping):
    cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--limit", "500"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("从飞书拉取数据失败！")
        return None

    try:
        data_full = json.loads(res.stdout)
        data = data_full.get("data", {})
        records = data.get("data", [])
        field_ids = data.get("field_id_list", [])
        record_ids = data.get("record_id_list", [])

        idx_map = {fid: i for i, fid in enumerate(field_ids)}
        
        pulled_items = []
        for i, row in enumerate(records):
            rid = record_ids[i]
            
            def get_val(field_key):
                fid = F(field_key)
                if not fid: return None
                idx = idx_map.get(fid)
                if idx is not None and idx < len(row): return row[idx]
                return None

            local_id = get_val("local_id")
            if not local_id:
                # 飞书侧如果没有local_id就用feishu_id代替作为唯一标识
                local_id = f"item-lark-{rid[-8:]}"

            remote_cat_rids = extract_link_record_id(get_val("category_link"))
            cat_rid = remote_cat_rids[0] if remote_cat_rids else None

            sub_cat_name = get_val("sub_category")
            major_name = normalize_select(get_val("major"))
            if cat_rid:
                for k, v in mapping.items():
                    if v.get("record_id") == cat_rid:
                        sub_cat_name = k
                        major_name = v.get("major")
                        break

            remote_space_rids = extract_link_record_id(get_val("space_record_id"))
            space_rid = remote_space_rids[0] if remote_space_rids else None

            item = {
                "id": local_id,
                "name": get_val("name"),
                "category": major_name,
                "sub_category": sub_cat_name,
                "category_record_id": cat_rid,
                "space_record_id": space_rid,
                "location": get_val("location"),
                "container": get_val("container"),
                "remark": get_val("remark"),
                "status": normalize_select(get_val("status")) or "正常",
                "updated_at": get_val("updated_at") or datetime.now().isoformat(),
                "feishu_record_id": rid,
            }
            pulled_items.append(item)
        return pulled_items
    except Exception as e:
        print(f"数据解析失败: {e}")
        return None

def sync():
    mapping = load_category_mapping()
    fm = load_field_mapping()
    F = lambda key: get_field_id(fm, "items", key)

    print("↓ 正在从飞书全量拉取数据作为唯一数据源...")
    pulled_items = get_feishu_records(F, mapping)
    
    if pulled_items is not None:
        items_data = {"items": pulled_items}
        with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
            json.dump(items_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 拉取成功！本地 items.json 已被全量覆盖，共 {len(pulled_items)} 条。")
    else:
        print("❌ 拉取失败，已保留本地原数据。")

if __name__ == "__main__":
    sync()