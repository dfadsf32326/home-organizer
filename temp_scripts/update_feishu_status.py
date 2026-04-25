import json
import subprocess
import os

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
TABLE_ID = "tbluMVXBpHIJDGyi"

# 更新刚才推上去的7条记录的状态为 "盘点中"
# 从 items.json 获取刚才推送记录的 feishu_record_id (基于 name 匹配)
with open("data/items.json", "r", encoding="utf-8") as f:
    items = json.load(f).get("items", [])

target_names = [
    "一张身份证复印件", 
    "两张身份证、户口本复印件", 
    "活动公司的试用员工合同", 
    "商业保密协议", 
    "活动公司的离职证明", 
    "泛微的劳动合同", 
    "泛微的终止劳动合同协议书"
]

updated_count = 0
for item in items:
    if item["name"] in target_names and item.get("feishu_record_id"):
        feishu_id = item["feishu_record_id"]
        # F29 is status 
        fields = {"F29": ["盘点中"]}
        
        cmd = [LARK_CLI, "base", "+record-update", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--record-id", feishu_id, "--json", json.dumps(fields, ensure_ascii=False)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"Updated {item['name']} status to 盘点中")
            updated_count += 1
        else:
            print(f"Failed to update {item['name']}: {res.stderr}")

if updated_count > 0:
    print("Triggering sync...")
    subprocess.run(["python3", "scripts/sync_final.py"])
