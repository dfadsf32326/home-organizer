import json
import subprocess
import os

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
SPACE_TABLE_ID = "tbl2cA30WNdkjsLS"

print("Fetching records from lark...")
cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", SPACE_TABLE_ID, "--limit", "1000"]
res = subprocess.run(cmd, capture_output=True, text=True)

if res.returncode != 0:
    print("Error fetching records:")
    print(res.stderr)
    exit(1)

try:
    data = json.loads(res.stdout)
except Exception as e:
    print("JSON decode error:", e)
    exit(1)

records = data.get("data", {}).get("items", [])
if not records:
    # 兼容另一种结构
    records = []
    rows = data.get("data", {}).get("data", [])
    for row in rows:
        # 手动解析返回的数据结构
        # ["name", null, {"id": "rid", "type": "url", "text": "link"}, ...]
        rid = None
        for item in row:
            if isinstance(item, str) and item.startswith("recvh"):
                rid = item
                break
        
        # 尝试通过别的途径解析名字等
        name = ""
        for item in row:
            if isinstance(item, str) and not item.startswith("recvh") and not item.startswith("space_") and "2026-" not in item and len(item)>2:
                name = item
                break
        
        if rid and name:
            records.append({
                "record_id": rid,
                "fields": {
                    "fldkM1d7q9": name # 假设 fldkM1d7q9 是名称字段（根据之前经验）
                }
            })

if not records:
    print("No records found or parsed.")
    print(str(data)[:500])
    exit(1)

print(f"Got {len(records)} records from remote.")

# 将所有的 records 保存为一个本地 JSON，方便后续查看
with open("data/remote_spaces_raw.json", "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

