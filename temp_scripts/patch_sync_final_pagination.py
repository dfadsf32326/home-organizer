import json
import subprocess
import os

file_path = os.path.expanduser("~/.hermes/skills/custom/home-organizer/scripts/sync_final.py")

with open(file_path, 'r') as f:
    content = f.read()

# Replace the get_feishu_records function to support pagination
old_get_records = '''def get_feishu_records(F, mapping):
    cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--limit", "500"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("从飞书拉取数据失败！")
        return None'''

new_get_records = '''def get_feishu_records(F, mapping):
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
            
            if not has_more or len(records) < page_size:
                break
            
            offset += len(records)
        except Exception as e:
            print(f"数据解析失败: {e}")
            return None
    
    # Reconstruct the data structure expected by the rest of the function
    data = {"data": all_records, "field_id_list": all_field_ids, "record_id_list": all_record_ids}'''

content = content.replace(old_get_records, new_get_records)

with open(file_path, 'w') as f:
    f.write(content)

print("Patch applied: Added pagination support to sync_final.py")
