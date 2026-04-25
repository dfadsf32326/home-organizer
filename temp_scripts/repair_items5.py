import json
import subprocess
import os

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
TABLE_ID = "tbluMVXBpHIJDGyi"

cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--limit", "500"]
res = subprocess.run(cmd, capture_output=True, text=True)
rj = json.loads(res.stdout)
if not rj.get("ok"):
    print("Error:", rj)
else:
    items = rj.get("data", {}).get("items", [])
    print("Found items count:", len(items))
    if items:
        print("First item:", items[0].get("fields", {}).get("fldkM1d7q9"))
