import json
import subprocess
import os

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
TABLE_ID = "tblvV901a16Wq8H2" # Space table
cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--limit", "500"]
res = subprocess.run(cmd, capture_output=True, text=True)

try:
    data_list = json.loads(res.stdout).get("data", {}).get("data", [])
    print(f"Total spaces: {len(data_list)}")
    
    # 找名字索引
    name_idx = None
    rid_idx = None
    if len(data_list) > 0:
        for i, val in enumerate(data_list[0]):
            if isinstance(val, str) and val.startswith("recv"):
                rid_idx = i
            elif isinstance(val, str) and val in ["暂存区", "我的病历相关文件袋", "客厅"]:
                name_idx = i
                
        # print("First row:", data_list[0])
    
    if name_idx is not None and rid_idx is not None:
        for row in data_list:
            rid = row[rid_idx]
            name = row[name_idx]
            if rid in ["recvhN14HPrYMU", "recvhMXUk94xEj"]:
                print(f"Found match: {name} -> {rid}")
except Exception as e:
    print("Error:", e)
    print("Output preview:", res.stdout[:200])

