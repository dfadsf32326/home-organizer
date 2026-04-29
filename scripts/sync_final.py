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
    all_records = []
    all_field_ids = []
    all_record_ids = []
    offset = 0
    page_size = 500
    
    while True:
        cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--limit", str(page_size), "--offset", str(offset)]
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
            has_more = data.get("has_more", False)
            
            all_records.extend(records)
            all_field_ids = field_ids  # field_ids should be same for all pages
            all_record_ids.extend(record_ids)
            
            print(f"  已拉取 {len(all_records)} 条记录...")
            
            if not has_more:
                break
            
            offset += len(records)
        except Exception as e:
            print(f"数据解析失败: {e}")
            return None
    
    # Now process all accumulated data
    idx_map = {fid: i for i, fid in enumerate(all_field_ids)}
    
    pulled_items = []
    for i, row in enumerate(all_records):
        rid = all_record_ids[i]
        
        def get_val(field_key):
            fid = F(field_key)
            if not fid: return None
            idx = idx_map.get(fid)
            if idx is not None and idx < len(row): return row[idx]
            return None

        local_id = get_val("local_id")
        if not local_id:
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

        location_val = None
        container_val = None
        
        if space_rid:
            try:
                with open(os.path.join(PROJECT_ROOT, "data/space_tree.json"), "r") as sf:
                    stree = json.load(sf)
                    nodes = stree.get("nodes", [])
                    node_map = {n.get("id"): n for n in nodes if n.get("id")}
                    for space_data in nodes:
                        if space_data.get("record_id") == space_rid or space_data.get("id") == space_rid:
                            if space_data.get("type") in ["容器", "未分类"]:
                                container_val = space_data.get("name")
                                parent_id = space_data.get("parent_id")
                                if parent_id and parent_id in node_map:
                                    location_val = node_map[parent_id].get("name")
                            else:
                                location_val = space_data.get("name")
                            break
            except:
                pass
        
        if not location_val and not container_val:
            location_val = get_val("location")
            container_val = get_val("container")

        item = {
            "id": local_id,
            "name": get_val("name"),
            "category": major_name,
            "sub_category": sub_cat_name,
            "category_record_id": cat_rid,
            "space_record_id": space_rid,
            "location": location_val,
            "container": container_val,
            "remark": get_val("remark"),
            "status": normalize_select(get_val("status")) or "正常",
            "updated_at": get_val("updated_at") or datetime.now().isoformat(),
            "feishu_record_id": rid,
        }
        pulled_items.append(item)
    return pulled_items


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