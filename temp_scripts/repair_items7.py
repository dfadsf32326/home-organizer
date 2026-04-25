import json
import subprocess
import os

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
TABLE_ID = "tbluMVXBpHIJDGyi"

cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--limit", "500"]
res = subprocess.run(cmd, capture_output=True, text=True)
rj = json.loads(res.stdout)
data_list = rj.get("data", {}).get("data", [])
fields_list = rj.get("data", {}).get("fields", [])

name_idx = fields_list.index("物品名称")
space_idx = fields_list.index("容器")
rid_idx = fields_list.index("记录 ID")

print("Total records:", len(data_list))

count = 0
for row in data_list:
    name = row[name_idx]
    if "病历" in name or "体检" in name or "报告" in name or "化验" in name or "眼科" in name or "保险" in name or "合同" in name or "保单" in name or "车险" in name:
        count += 1
        print(f"Name: {name}, Space: {row[space_idx]}, RID: {row[rid_idx]}")
print(f"Matched records: {count}")
