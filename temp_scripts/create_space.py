import json
import subprocess
import os

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
TABLE_ID = "tbl2cA30WNdkjsLS"

fields = {
    "fld3jffiay": "病历相关文件袋",
    "flddMrA84a": "收纳工具"
}

cmd = [LARK_CLI, "base", "+record-upsert", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--json", json.dumps(fields, ensure_ascii=False)]
res = subprocess.run(cmd, capture_output=True, text=True)

if res.returncode == 0:
    print("✅ 飞书空间创建成功！")
    output = json.loads(res.stdout)
    print(f"Record ID: {output.get('record_id')}")
    # Trigger space sync to update local tree
    subprocess.run(["python3", "scripts/sync_spaces_bidirectional.py"])
else:
    print(f"❌ 创建失败: {res.stderr}")

