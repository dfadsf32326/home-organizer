import json
import subprocess
import os

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
SPACE_TABLE_ID = "tbl2cA30WNdkjsLS"
SPACE_TREE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "space_tree.json")

def pull_spaces():
    print("1. 拉取飞书全量空间数据...")
    cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", SPACE_TABLE_ID, "--limit", "500"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error fetching spaces: {res.stderr}")
        return

    data_full = json.loads(res.stdout)
    # 根据之前测试的结构：data -> data -> [ [field_values...], ...] 或者直接看 fields
    # 但是使用 --json 或者观察 record_id_list 更准确
    
    # 获取原始记录，避免格式不一致，更好的方式是带上具体参数，但我们直接解析
    # 最稳妥：从原始数据重新构造请求以防 lark-cli 版本导致的格式变化，这里直接使用已知结构
    records = []
    if "data" in data_full and "data" in data_full["data"]:
        # lark-cli record-list returns "data": { "data": [ [...] ], "record_id_list": [...] }
        rows = data_full["data"]["data"]
        rids = data_full["data"]["record_id_list"]
        for i, row in enumerate(rows):
            # 字段顺序根据之前观察：
            # 0: 名称, 1: ?, 2: [状态], 3: ?, 4: [类型], 5: ?, 6: [使用率], 7: 主要功能, 8: [父空间...]
            
            name = row[0] if len(row) > 0 and row[0] else ""
            status = row[2][0] if len(row) > 2 and row[2] else ""
            typ = row[4][0] if len(row) > 4 and row[4] else ""
            freq = row[6][0] if len(row) > 6 and row[6] else ""
            activity = row[7] if len(row) > 7 and row[7] else ""
            
            parent_rid = None
            if len(row) > 8 and isinstance(row[8], list) and len(row[8]) > 0:
                parent_rid = row[8][0].get("id") if isinstance(row[8][0], dict) else None

            records.append({
                "record_id": rids[i],
                "name": name,
                "type": typ,
                "status": status,
                "frequency": freq,
                "primary_activity": activity,
                "parent_rid": parent_rid
            })

    if not records:
        print("未获取到空间记录，或者解析失败。")
        return

    out_data = {"version": "1.0", "data": records}
    with open(SPACE_TREE_FILE, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)
    print(f"✅ 成功覆盖 space_tree.json，共保留 {len(records)} 个节点。")

if __name__ == "__main__":
    pull_spaces()
