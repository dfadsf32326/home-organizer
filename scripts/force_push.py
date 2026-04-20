import json
import subprocess
import os
import time

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
TABLE_ID = "tbluMVXBpHIJDGyi"
PROJECT_ROOT = "/Users/robinlu/Self-established_skill/home-organizer"
ITEMS_FILE = os.path.join(PROJECT_ROOT, "data/items.json")

def force_push():
    with open(ITEMS_FILE, 'r', encoding='utf-8') as f:
        items_data = json.load(f)
    
    items = items_data.get("items", [])
    success = 0
    fail = 0
    
    # 只推送那些没有 record_id 的项
    to_push = [it for it in items if not it.get("feishu_record_id")]
    print(f"🚀 开始强力推送 {len(to_push)} 个新物品...")

    for i, item in enumerate(to_push):
        fields = {
            "物品名称": item.get("name"),
            "大类": [item.get("category")] if item.get("category") else [],
            "子分类": item.get("sub_category"),
            "位置": item.get("location"),
            "容器": item.get("container"),
            "本地数据库ID": item.get("id")
        }
        
        # 使用 +record-create 而不是 upsert，最稳妥
        cmd = [
            LARK_CLI, "base", "+record-create",
            "--base-token", BASE_TOKEN,
            "--table-id", TABLE_ID,
            "--json", json.dumps(fields, ensure_ascii=False)
        ]
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            try:
                rj = json.loads(res.stdout)
                # create 的返回结构通常是 data.record.record_id
                rid = rj.get("data", {}).get("record", {}).get("record_id")
                if rid:
                    item["feishu_record_id"] = rid
                    success += 1
                else:
                    # 尝试另一种结构
                    rid_list = rj.get("data", {}).get("record_id_list")
                    if rid_list:
                        item["feishu_record_id"] = rid_list[0]
                        success += 1
            except:
                success += 1 # 命令成功了就算成功
        else:
            print(f"Failed {item.get('name')}: {res.stderr}")
            fail += 1
        
        if (i+1) % 10 == 0:
            print(f"进度: {i+1}/{len(to_push)}...")
            # 每10个保存一次，防止中途奔溃
            with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
                json.dump(items_data, f, ensure_ascii=False, indent=2)

    # 最终保存
    with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(items_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 推送完成！成功: {success}, 失败: {fail}")

if __name__ == "__main__":
    force_push()
