import json
import subprocess
import os
from datetime import datetime

# 配置路径
LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN="PS56bPhyNaWXRdsJX78cxyIOnJb"
TABLE_ID = "tbluMVXBpHIJDGyi"
PROJECT_ROOT = "/Users/robinlu/Self-established_skill/home-organizer"
ITEMS_FILE = os.path.join(PROJECT_ROOT, "data/items.json")

def get_feishu_records():
    """获取飞书云端所有记录及其详情"""
    cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--limit", "500"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error fetching records: {res.stderr}")
        return {}
    
    mapping = {}
    try:
        data_full = json.loads(res.stdout)
        data = data_full.get("data", {})
        records = data.get("data", [])
        field_names = data.get("fields", [])
        record_ids = data.get("record_id_list", [])
        
        # 获取各字段索引
        def get_idx(name):
            return field_names.index(name) if name in field_names else None

        indices = {
            "id": get_idx("本地数据库ID"),
            "name": get_idx("物品名称"),
            "category": get_idx("大类"),
            "sub_category": get_idx("子分类"),
            "location": get_idx("位置"),
            "container": get_idx("容器")
        }

        for i, row in enumerate(records):
            local_id = row[indices["id"]] if indices["id"] is not None and indices["id"] < len(row) else None
            if local_id:
                if local_id not in mapping:
                    mapping[local_id] = []
                
                # 提取云端详情
                remote_data = {
                    "record_id": record_ids[i],
                    "name": row[indices["name"]] if indices["name"] is not None else None,
                    "category": row[indices["category"]] if indices["category"] is not None else None,
                    "sub_category": row[indices["sub_category"]] if indices["sub_category"] is not None else None,
                    "location": row[indices["location"]] if indices["location"] is not None else None,
                    "container": row[indices["container"]] if indices["container"] is not None else None,
                }
                mapping[local_id].append(remote_data)
    except Exception as e:
        print(f"Error parsing remote records: {e}")
    return mapping


def sync():
    if not os.path.exists(ITEMS_FILE):
        print(f"Error: {ITEMS_FILE} missing")
        return

    with open(ITEMS_FILE, 'r', encoding='utf-8') as f:
        items_data = json.load(f)
    
    items_list = items_data.get("items", [])
    print(f"🔄 正在运行双向同步 (处理 {len(items_list)} 个物品)...")

    feishu_map = get_feishu_records()
    success_count = 0

    for item in items_list:
        local_id = item.get("id")
        if not local_id: continue

        # 判断是更新还是新增
        remote_records = feishu_map.get(local_id, [])
        target_rid = None
        
        if remote_records:
            # 逻辑 A：云端反向同步 (Cloud -> Local)
            # 规则：如果云端的位置或容器发生了变化，先同步到本地
            remote_main = remote_records[0]
            target_rid = remote_main["record_id"]
            
            changed = False
            # 云端位置变更
            if remote_main["location"] and remote_main["location"] != item.get("location"):
                print(f"发现云端变动：{item.get('name')} 的位置 [{item.get('location')}] -> [{remote_main['location']}]")
                item["location"] = remote_main["location"]
                changed = True
            
            # 云端容器变更
            if remote_main["container"] and remote_main["container"] != item.get("container"):
                print(f"发现云端变动：{item.get('name')} 的容器 [{item.get('container')}] -> [{remote_main['container']}]")
                item["container"] = remote_main["container"]
                changed = True
            
            if changed:
                item["updated_at"] = datetime.now().isoformat()

            # 如果有多个重复记录，清理多余的
            if len(remote_records) > 1:
                print(f"发现重复项：清理 {item.get('name')} 的多余云端记录...")
                for extra in remote_records[1:]:
                    subprocess.run([LARK_CLI, "base", "+record-delete", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--record-id", extra["record_id"], "--yes"])

        # 构造飞书字段映射 (执行更新/推送)
        fields = {
            "物品名称": item.get("name"),
            "大类": [item.get("category")] if item.get("category") else [],
            "子分类": item.get("sub_category"),
            "位置": item.get("location"),
            "容器": item.get("container"),
            "本地数据库ID": local_id,
            "状态": [item.get("status", "active")]
        }

        cmd = [
            LARK_CLI, "base", "+record-upsert",
            "--base-token", BASE_TOKEN,
            "--table-id", TABLE_ID,
            "--json", json.dumps(fields, ensure_ascii=False)
        ]

        if target_rid:
            cmd.extend(["--record-id", target_rid])
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            try:
                res_json = json.loads(res.stdout)
                # 结构通常是 data.record.record_id_list[0]
                new_rid = (res_json.get("data", {}).get("record", {}).get("record_id_list") or [None])[0]
                
                if new_rid:
                    item["feishu_record_id"] = new_rid
                    if not target_rid: # 如果是新增，更新时间戳
                        item["updated_at"] = datetime.now().isoformat()
                    success_count += 1
            except Exception as e:
                success_count += 1
        else:
            print(f"Sync failed for {item.get('name')}: {res.stderr}")


    # 保存更新后的本地数据
    with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(items_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 同步完成！共处理 {success_count} 个物品。")

if __name__ == "__main__":
    sync()
