import json
import subprocess
import os
from datetime import datetime

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
TABLE_ID = "tbluMVXBpHIJDGyi"
PENDING_FILE = "/Users/robinlu/Self-established_skill/home-organizer/data/pending_migration.json"

def batch_sync():
    if not os.path.exists(PENDING_FILE):
        print("Pending file not found.")
        return

    with open(PENDING_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    pending_items = data.get("pending_items", [])
    if not pending_items:
        print("No items to sync.")
        return

    print(f"Preparing to sync {len(pending_items)} items to Feishu via batch upsert...")

    # Prepare records for batch upsert
    # Standard: mapping local fields to Feishu field names
    records_to_upsert = []
    for item in pending_items:
        fields = {
            "物品名称": item.get("name"),
            "大类": [item.get("category")] if item.get("category") else [],
            "子分类": item.get("sub_category"),
            "位置": item.get("location"),
            "容器": item.get("container"),
            "本地数据库ID": item.get("id"),
            "状态": [item.get("status", "active")]
        }
        records_to_upsert.append(fields)

    # lark-cli base +record-batch-upsert --json '[{fields...}, ...]'
    # To avoid command line length limits, we'll process in chunks of 50
    chunk_size = 50
    all_new_record_ids = []
    
    for i in range(0, len(records_to_upsert), chunk_size):
        chunk = records_to_upsert[i:i + chunk_size]
        print(f"Syncing chunk {i//chunk_size + 1} ({len(chunk)} items)...")
        
        cmd = [
            LARK_CLI, "base", "+record-batch-upsert",
            "--base-token", BASE_TOKEN,
            "--table-id", TABLE_ID,
            "--json", json.dumps(chunk, ensure_ascii=False)
        ]
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            try:
                res_data = json.loads(res.stdout)
                # The upsert returns a list of record IDs in the same order
                record_ids = res_data.get("data", {}).get("record_id_list", [])
                all_new_record_ids.extend(record_ids)
            except Exception as e:
                print(f"Error parsing response: {e}")
                # Fill with None to maintain index
                all_new_record_ids.extend([None] * len(chunk))
        else:
            print(f"Batch upsert failed: {res.stderr}")
            all_new_record_ids.extend([None] * len(chunk))

    # Update local pending_migration.json with the record IDs
    for j, rid in enumerate(all_new_record_ids):
        if j < len(pending_items) and rid:
            pending_items[j]["feishu_record_id"] = rid
            pending_items[j]["updated_at"] = datetime.now().isoformat()

    with open(PENDING_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Successfully synced {len([r for r in all_new_record_ids if r])} items.")

if __name__ == "__main__":
    batch_sync()
