import json
import subprocess
import os
from datetime import datetime
import time

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
TABLE_ID = "tbluMVXBpHIJDGyi"
PENDING_FILE = "/Users/robinlu/Self-established_skill/home-organizer/data/pending_migration.json"

def sync_individual():
    if not os.path.exists(PENDING_FILE):
        print("Pending file not found.")
        return

    with open(PENDING_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    pending_items = data.get("pending_items", [])
    if not pending_items:
        print("No items to sync.")
        return

    print(f"Syncing {len(pending_items)} items individually using +record-upsert...")

    success_count = 0
    for i, item in enumerate(pending_items):
        # 构造符合新标准的字段
        fields = {
            "物品名称": item.get("name"),
            "大类": [item.get("category")] if item.get("category") else [],
            "子分类": item.get("sub_category"),
            "位置": item.get("location"),
            "容器": item.get("container"),
            "本地数据库ID": item.get("id"),
            "状态": [item.get("status", "active")]
        }

        # 飞书 upsert 逻辑：如果存在 本地数据库ID 则更新，否则创建
        cmd = [
            LARK_CLI, "base", "+record-upsert",
            "--base-token", BASE_TOKEN,
            "--table-id", TABLE_ID,
            "--json", json.dumps(fields, ensure_ascii=False)
        ]
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            try:
                res_data = json.loads(res.stdout)
                # 获取 record_id 并保存
                rid = res_data.get("data", {}).get("record_id_list", [None])[0]
                if rid:
                    item["feishu_record_id"] = rid
                    item["updated_at"] = datetime.now().isoformat()
                    success_count += 1
                    if i % 10 == 0:
                        print(f"Progress: {i}/{len(pending_items)} synced...")
            except:
                print(f"Error parsing response for: {item.get('name')}")
        else:
            print(f"Failed to sync {item.get('name')}: {res.stderr}")
        
        # 稍微停顿，防止触发 API 频率限制（虽然 lark-cli 有重试，但稳一点好）
        time.sleep(0.1)

    with open(PENDING_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Final: Successfully synced {success_count}/{len(pending_items)} items.")

if __name__ == "__main__":
    sync_individual()
