#!/usr/bin/env python3
import json
import subprocess
import os
import time

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = os.environ.get("LARK_BASE_TOKEN")
SPACE_TABLE_ID = "tbl2cA30WNdkjsLS"
ITEMS_TABLE_ID = "tbluMVXBpHIJDGyi"

PROJECT_ROOT = "/Users/robinlu/Self-established_skill/home-organizer"
SPACE_TREE_FILE = os.path.join(PROJECT_ROOT, "data", "space_tree.json")
ITEMS_FILE = os.path.join(PROJECT_ROOT, "data", "items.json")
FIELD_MAPPING_FILE = os.path.join(PROJECT_ROOT, "data", "field_mapping.json")

def load_field_mapping():
    with open(FIELD_MAPPING_FILE, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    spaces_fields = mapping.get('tables', {}).get('spaces', {}).get('fields', {})
    items_fields = mapping.get('tables', {}).get('items', {}).get('fields', {})
    return {k: v['feishu_id'] for k, v in spaces_fields.items()}, items_fields.get("space_link", {}).get("feishu_id")

def generate_id(name, prefix=""):
    import hashlib
    # Generate a stable short ID based on name to prevent duplicates
    hash_str = hashlib.md5(name.encode('utf-8')).hexdigest()[:8]
    if prefix:
        return f"{prefix}_{hash_str}"
    return f"spc_{hash_str}"

def main():
    print("1. 分析缺失的容器节点...")
    with open(ITEMS_FILE, 'r', encoding='utf-8') as f:
        items_data = json.load(f)
    with open(SPACE_TREE_FILE, 'r', encoding='utf-8') as f:
        space_data = json.load(f)

    existing_space_names = {n.get("name"): n for n in space_data.get("nodes", [])}
    
    # 找出所有在 items 的 container 字段里有，但没在 space_tree 里的容器
    missing_containers = {} # container_name -> parent_location_name
    for item in items_data.get("items", []):
        if item.get("status") == "deleted": continue
        cont = item.get("container", "").strip()
        loc = item.get("location", "").strip()
        if cont and cont not in existing_space_names:
            # Prefer a specific location, fallback to '暂存区' if none provided
            missing_containers[cont] = loc if loc else "暂存区"
            
    if not missing_containers:
        print("没有发现缺失的容器，直接进行重新关联。")
    else:
        print(f"发现 {len(missing_containers)} 个缺失的容器。开始创建并推送到飞书空间表...")
        
        spaces_key_to_fld, _ = load_field_mapping()
        
        for cont_name, parent_loc_name in missing_containers.items():
            parent_node = existing_space_names.get(parent_loc_name)
            if not parent_node:
                # 理论上之前脚本里跑过 loc 的去重，所以这里大概率都能找到 parent_loc_name
                # 如果没有，强制挂到 暂存区 或 根节点
                parent_node = existing_space_names.get("暂存区")
                
            new_node = {
                "id": generate_id(cont_name, "bag"),
                "name": cont_name,
                "parent_id": parent_node.get("id") if parent_node else None,
                "type": "container",
                "notes": "自动提取自物品明细的 container 字段"
            }
            
            # 推送到飞书
            fields_to_update = {
                spaces_key_to_fld["name"]: cont_name,
                spaces_key_to_fld["type"]: "容器",
                spaces_key_to_fld["id"]: new_node["id"]
            }
            if parent_node and parent_node.get("record_id"):
                fields_to_update[spaces_key_to_fld["parent_id"]] = [parent_node["record_id"]]
                
            print(f"  ➕ 创建容器: {cont_name} (挂载于: {parent_loc_name})")
            cmd = [LARK_CLI, "base", "+record-upsert", "--base-token", BASE_TOKEN, "--table-id", SPACE_TABLE_ID, "--json", json.dumps(fields_to_update, ensure_ascii=False)]
            res = subprocess.run(cmd, capture_output=True, text=True)
            
            if res.returncode == 0:
                rj = json.loads(res.stdout)
                new_rid = rj.get("data", {}).get("record", {}).get("record_id")
                if not new_rid:
                    new_rid = (rj.get("data", {}).get("record_id_list") or [None])[0]
                if new_rid:
                    new_node["record_id"] = new_rid
                    space_data["nodes"].append(new_node)
                    existing_space_names[cont_name] = new_node
                    print(f"    ✅ 成功回写 record_id: {new_rid}")
            else:
                print(f"    ❌ 创建失败: {res.stderr.strip()}")
            time.sleep(0.05)

        print("\n2. 保存更新后的 space_tree.json...")
        with open(SPACE_TREE_FILE, 'w', encoding='utf-8') as f:
            json.dump(space_data, f, ensure_ascii=False, indent=2)


    print("\n3. 依据最高优先级 (container 字段) 重新执行物品到容器的关联推拉...")
    _, items_space_link_fld = load_field_mapping()
    
    updated_count = 0
    for item in items_data.get("items", []):
        item_rid = item.get("feishu_record_id")
        if not item_rid or item.get("status") == "deleted": continue
        
        # 核心改动：把 container 的优先级提至最高！
        cont_name = item.get("container", "").strip()
        loc_name = item.get("location", "").strip()
        
        target_space_node = None
        if cont_name:
            target_space_node = existing_space_names.get(cont_name)
        elif loc_name:
            target_space_node = existing_space_names.get(loc_name)
            
        if target_space_node and target_space_node.get("record_id"):
            target_space_rid = target_space_node["record_id"]
            
            # 如果本地记录的关联不同，就进行更新推送
            if item.get("space_record_id") != target_space_rid:
                item["space_record_id"] = target_space_rid
                item["space_id"] = target_space_node.get("id")
                
                fields_to_update = {
                    items_space_link_fld: [target_space_rid]
                }
                cmd = [LARK_CLI, "base", "+record-upsert", "--base-token", BASE_TOKEN, "--table-id", ITEMS_TABLE_ID, "--record-id", item_rid, "--json", json.dumps(fields_to_update, ensure_ascii=False)]
                subprocess.run(cmd, capture_output=True)
                updated_count += 1
                print(f"  🔗 重新对齐关联: {item.get('name')} -> {target_space_node.get('name')} ({target_space_rid})")
                time.sleep(0.05)
                
    if updated_count > 0:
        print("\n4. 保存重新关联后的 items.json...")
        with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
            json.dump(items_data, f, ensure_ascii=False, indent=2)
            
    print(f"\n🎉 空间对齐与重关联完成！共补齐并创建了 {len(missing_containers) if missing_containers else 0} 个容器，更新了 {updated_count} 个物品的精确定位关联。")

if __name__ == '__main__':
    main()
