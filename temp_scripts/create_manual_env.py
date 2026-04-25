import json
import subprocess
import os

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
CATEGORY_TABLE_ID = "tbl6Ew6fmmhqeeSP"

cmd_category = [
    LARK_CLI, "base", "+record-upsert", 
    "--base-token", BASE_TOKEN, 
    "--table-id", CATEGORY_TABLE_ID, 
    "--json", json.dumps({"fldx2lVHJB": "说明书与保修卡", "fldwGw0lkN": "📚 文档资产"})
]
res_category = subprocess.run(cmd_category, capture_output=True, text=True)
if res_category.returncode == 0:
    print("✅ 分类 '说明书与保修卡' 创建成功！")
    print("触发全量同步逻辑...")
    subprocess.run(["python3", "scripts/sync_spaces_bidirectional.py"])
    subprocess.run(["python3", "scripts/sync_category_mapping.py"])
else:
    print(f"❌ 分类创建失败: {res_category.stderr}")

