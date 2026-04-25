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
    if not current_space:
        print(f"Empty space: {name}")
