import json
import subprocess
import os

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = os.environ.get("LARK_BASE_TOKEN")
TABLE_ID = "tbluMVXBpHIJDGyi"

def load_items():
    with open("/Users/robinlu/.hermes/skills/home-organizer/data/items.json", "r") as f:
        return json.load(f)

def load_fm():
    with open("/Users/robinlu/.hermes/skills/home-organizer/data/field_mapping.json", "r") as f:
        return json.load(f)

items = load_items()["items"]
fm = load_fm()
status_id = fm["tables"]["items"]["fields"]["status"]["feishu_id"]

# 找出那 31 个刚修正的物品并推送到飞书
updated = 0
for item in items:
    rid = item.get("feishu_record_id")
    if not rid:
        continue
    
    # 我们知道我们刚把状态设为 "正常"
    if item.get("status") == "正常" and item.get("container_id") == "手机电子产品配件箱":
        # 或者刚加进去的那两批
        fields = {
            status_id: ["正常"]
        }
        cmd = [
            LARK_CLI, "base", "+record-upsert",
            "--base-token", BASE_TOKEN,
            "--table-id", TABLE_ID,
            "--record-id", rid,
            "--json", json.dumps(fields, ensure_ascii=False)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            updated += 1
        else:
            print(f"Update failed for {item.get('name')}")

print(f"Force pushed status update for {updated} items.")
