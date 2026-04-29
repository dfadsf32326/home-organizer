import json
import subprocess
import os

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
TABLE_ID = "tbluMVXBpHIJDGyi"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STAGING_FILE = os.path.join(PROJECT_ROOT, "data/staging/staging_items.json")
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

def push_staging():
    if not os.path.exists(STAGING_FILE):
        print("暂无需要推送的 staging 数据。")
        return

    with open(STAGING_FILE, 'r', encoding='utf-8') as f:
        staging_data = json.load(f)
        
    items = staging_data if isinstance(staging_data, list) else staging_data.get("items", [])
    if not items:
        print("暂无需要推送的 staging 数据。")
        return
        
    fm = load_field_mapping()
    F = lambda key: get_field_id(fm, "items", key)
    
    success_count = 0
    print(f"开始推送 {len(items)} 条暂存数据到飞书...")
    
    for item in items:
        fields = {
            F("name"):          item.get("name"),
            F("sub_category"):  item.get("sub_category"),
            F("location"):      item.get("location"),
            F("container"):     item.get("container"),
            F("remark"):        item.get("remark"),
            F("local_id"):      item.get("id"),
        }
        
        cat_rid = item.get("category_record_id")
        if cat_rid:
            fields[F("category_link")] = [{"id": cat_rid}]

        space_rid = item.get("space_record_id")
        if space_rid:
            fields[F("space_record_id")] = [{"id": space_rid}]

        status = item.get("status") or ["盘点中"]
        fields[F("status")] = [status] if isinstance(status, str) else status

        cmd = [LARK_CLI, "base", "+record-upsert", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--json", json.dumps(fields, ensure_ascii=False)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        
        if res.returncode == 0:
            print(f"↑ 推送成功: {item.get('name')}")
            success_count += 1
        else:
            print(f"❌ 推送失败 ({item.get('name')}): {res.stderr}")
            
    if success_count == len(items):
        print("✅ 全部暂存数据推送完成！正在清空暂存区...")
        os.remove(STAGING_FILE)
        
        print("↓ 正在触发全量拉取同步...")
        sync_cmd = ["python3", os.path.join(PROJECT_ROOT, "scripts/sync_final.py")]
        subprocess.run(sync_cmd)
    else:
        print(f"⚠️ 部分推送失败，保留 staging_items.json 供检查，成功 {success_count}/{len(items)}。")

if __name__ == "__main__":
    push_staging()
