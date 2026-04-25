import json
import subprocess
import os

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
TABLE_ID = "tblvV901a16Wq8H2" # Space table
cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--limit", "500"]
res = subprocess.run(cmd, capture_output=True, text=True)
items = json.loads(res.stdout).get("data", {}).get("items", [])
mapping = {}
for i in items:
    fields = i.get("fields", {})
    name = fields.get("fldkM1d7q9", "")
    rid = i.get("record_id", "")
    mapping[rid] = name

print("recvhN14HPrYMU:", mapping.get("recvhN14HPrYMU"))
print("recvhMXUk94xEj:", mapping.get("recvhMXUk94xEj"))

