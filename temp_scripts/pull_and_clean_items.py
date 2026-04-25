import json
import subprocess
import os

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
ITEM_TABLE_ID = "tbluMVXBpHIJDGyi"
ITEMS_FILE = "data/items.json"
FIELD_MAPPING_FILE = "data/field_mapping.json"

def load_field_mapping():
    with open(FIELD_MAPPING_FILE, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    fields = mapping.get('tables', {}).get('items', {}).get('fields', {})
    key_to_fld = {k: v['feishu_id'] for k, v in fields.items()}
    fld_to_key = {v['feishu_id']: k for k, v in fields.items()}
    return key_to_fld, fld_to_key

def pull_items():
    print("拉取飞书全量物品数据...")
    key_to_fld, fld_to_key = load_field_mapping()
    cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", ITEM_TABLE_ID, "--limit", "1000"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"❌ 拉取失败: {res.stderr}")
        return

    data_full = json.loads(res.stdout)
    records = data_full.get("data", {}).get("data", [])
    field_ids = data_full.get("data", {}).get("field_id_list", [])
    record_ids = data_full.get("data", {}).get("record_id_list", [])
    
    idx_to_key = {i: fld_to_key[fid] for i, fid in enumerate(field_ids) if fid in fld_to_key}
    
    remote_items = []
    for i, row in enumerate(records):
        rid = record_ids[i]
        item = {"feishu_record_id": rid}
        
        for idx, val in enumerate(row):
            if idx in idx_to_key:
                key = idx_to_key[idx]
                if val is not None:
                    # 针对关联字段：提取第一项的文本作为名称
                    if key == "space" and isinstance(val, list) and len(val)>0:
                        item["space"] = val[0].get("text")
                    elif isinstance(val, list) and len(val)>0 and isinstance(val[0], str):
                        item[key] = val[0]
                    else:
                        item[key] = val
        remote_items.append(item)
        
    out_data = {"version": "1.0", "items": remote_items}
    with open(ITEMS_FILE, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)
    print(f"✅ 成功覆盖 items.json，共保留 {len(remote_items)} 个物品 (已清除云端删除的记录)。")

if __name__ == "__main__":
    pull_items()
