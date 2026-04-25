import json
import subprocess
import os

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
TABLE_ID = "tbluMVXBpHIJDGyi"

cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--limit", "500"]
res = subprocess.run(cmd, capture_output=True, text=True)
items = json.loads(res.stdout).get("data", {}).get("items", [])

for item in items:
    fields = item.get("fields", {})
    name = fields.get("fldkM1d7q9", "")
    current_space = fields.get("fldyB3YQ1k", [])
    if "病历" in name or "体检" in name or "报告" in name or "化验" in name or "眼科" in name or "保险" in name or "合同" in name or "保单" in name or "车险" in name:
        print(f"Name: {name}, Space: {current_space}")
