import json
import subprocess
import os
import uuid
from datetime import datetime

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
TABLE_ID = "tbluMVXBpHIJDGyi"
CATEGORY_TABLE_ID = "tbl6Ew6fmmhqeeSP"
PROJECT_ROOT = "/Users/robinlu/Self-established_skill/home-organizer"
ITEMS_FILE = os.path.join(PROJECT_ROOT, "data/items.json")
MAPPING_FILE = os.path.join(PROJECT_ROOT, "data/category_mapping.json")


def load_category_mapping():
    """加载分类映射字典（子类名称 -> record_id）"""
    if not os.path.exists(MAPPING_FILE):
        print("⚠️  category_mapping.json 不存在，请先运行 sync_categories.py")
        return {}
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_time(t_str):
    if not t_str:
        return 0
    try:
        if isinstance(t_str, (int, float)):
            return float(t_str) / 1000.0
        return datetime.fromisoformat(t_str.replace('Z', '+00:00')).timestamp()
    except:
        return 0


def get_feishu_records():
    cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--limit", "500"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        return {}

    remote_data = {}
    try:
        data_full = json.loads(res.stdout)
        data = data_full.get("data", {})
        records = data.get("data", [])
        field_names = data.get("fields", [])
        record_ids = data.get("record_id_list", [])

        idx_map = {name: i for i, name in enumerate(field_names)}

        for i, row in enumerate(records):
            rid = record_ids[i]

            def get_val(fname):
                idx = idx_map.get(fname)
                if idx is not None and idx < len(row):
                    return row[idx]
                return None

            item_info = {
                "record_id": rid,
                "local_id": get_val("本地数据库ID"),
                "name": get_val("物品名称"),
                "category": get_val("大类"),
                "sub_category": get_val("子分类"),
                "category_link": get_val("分类表"),  # 关联字段的值
                "location": get_val("位置"),
                "container": get_val("容器"),
                "updated_at": get_val("更新时间"),
                "status": get_val("状态"),
                "remark": get_val("备注"),
            }
            remote_data[rid] = item_info
    except:
        pass
    return remote_data


def normalize_select(val):
    """归一化飞书 Select 字段（列表格式）为字符串"""
    if isinstance(val, list):
        return val[0] if val else None
    return val


def extract_link_record_id(link_val):
    """从关联字段值中提取 record_id 列表"""
    if not link_val:
        return []
    if isinstance(link_val, list):
        ids = []
        for item in link_val:
            if isinstance(item, dict):
                ids.append(item.get("id") or item.get("record_id"))
            elif isinstance(item, str):
                ids.append(item)
        return [x for x in ids if x]
    return []


def is_content_equal(local, remote, mapping):
    """深度比对本地物品内容和云端物品内容（含关联字段）"""
    checks = [
        (local.get("name"), remote.get("name")),
        (local.get("category"), normalize_select(remote.get("category"))),
        (local.get("sub_category"), remote.get("sub_category")),
        (local.get("location"), remote.get("location")),
        (local.get("container"), remote.get("container")),
        (local.get("status"), normalize_select(remote.get("status"))),
        (local.get("remark"), remote.get("remark")),
    ]

    # 关联字段比对
    local_cat_rid = local.get("category_record_id")
    remote_cat_rids = extract_link_record_id(remote.get("category_link"))
    remote_cat_rid = remote_cat_rids[0] if remote_cat_rids else None
    checks.append((local_cat_rid, remote_cat_rid))

    for l_val, r_val in checks:
        l_norm = l_val if l_val is not None else ""
        r_norm = r_val if r_val is not None else ""
        if str(l_norm).strip() != str(r_norm).strip():
            return False
    return True


def ensure_category_record_id(item, mapping):
    """确保物品有 category_record_id，如果没有则根据 sub_category 补齐"""
    sub_cat = item.get("sub_category")
    if not item.get("category_record_id") and sub_cat and sub_cat in mapping:
        item["category_record_id"] = mapping[sub_cat]["record_id"]
    return item


def sync():
    if not os.path.exists(ITEMS_FILE):
        return

    mapping = load_category_mapping()

    with open(ITEMS_FILE, 'r', encoding='utf-8') as f:
        items_data = json.load(f)

    local_items = items_data.get("items", [])
    print("正在拉取云端数据进行比对...")
    remote_data = get_feishu_records()

    processed_remote_rids = set()
    push_count = 0
    pull_count = 0
    skip_count = 0
    new_local_count = 0

    # 第一阶段：双向同步现有项
    for item in local_items:
        lid = item.get("id")
        rid = item.get("feishu_record_id")

        # 确保 category_record_id 存在
        ensure_category_record_id(item, mapping)

        # 匹配策略：优先 Record ID，其次本地 ID
        remote = remote_data.get(rid)
        if not remote:
            for r_rid, r_info in remote_data.items():
                if r_info["local_id"] == lid:
                    remote = r_info
                    rid = r_rid
                    item["feishu_record_id"] = rid
                    break

        if remote:
            processed_remote_rids.add(rid)
            local_ts = parse_time(item.get("updated_at"))
            remote_ts = parse_time(remote["updated_at"])

            # 深度内容比对（含关联字段）
            if is_content_equal(item, remote, mapping):
                skip_count += 1
                continue

            # 内容不一致，判断谁更晚
            if remote_ts > local_ts + 2:  # 2秒容差
                print(f"↓ 拉取更新: {item.get('name')}")
                item["name"] = remote["name"] or item["name"]
                item["location"] = remote["location"] or item["location"]
                item["container"] = remote["container"] or item["container"]
                item["sub_category"] = remote["sub_category"] or item.get("sub_category")
                item["remark"] = remote["remark"] or item.get("remark")
                item["category"] = normalize_select(remote["category"]) or item.get("category")
                item["status"] = normalize_select(remote["status"]) or item.get("status")

                # 拉取关联字段的 record_id
                remote_cat_rids = extract_link_record_id(remote.get("category_link"))
                if remote_cat_rids:
                    item["category_record_id"] = remote_cat_rids[0]

                item["updated_at"] = datetime.fromtimestamp(remote_ts).isoformat()
                pull_count += 1
                continue
            else:
                # 本地更新，准备推送
                pass

        # 推送逻辑 —— 核心改造：使用 category_record_id 建立到分类表的链接
        fields = {
            "物品名称": item.get("name"),
            "子分类": item.get("sub_category"),
            "位置": item.get("location"),
            "容器": item.get("container"),
            "备注": item.get("remark"),
            "本地数据库ID": lid,
        }

        # ★ 关联字段：使用 category_record_id 建立到分类表的链接（大类由飞书查找引用自动填充）
        cat_rid = item.get("category_record_id")
        if cat_rid:
            fields["分类表"] = cat_rid

        if item.get("status"):
            fields["状态"] = [item["status"]] if isinstance(item["status"], str) else item["status"]

        cmd = [LARK_CLI, "base", "+record-upsert", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--json", json.dumps(fields, ensure_ascii=False)]
        if rid:
            cmd.extend(["--record-id", rid])

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            push_count += 1
            try:
                rj = json.loads(res.stdout)
                res_data = rj.get("data", {})
                new_rid = (res_data.get("record_id_list") or [None])[0] or res_data.get("record", {}).get("record_id")
                if new_rid:
                    item["feishu_record_id"] = new_rid
                    processed_remote_rids.add(new_rid)
            except:
                pass
        else:
            print(f"Sync failed for {item.get('name')}: {res.stderr}")

    # 第二阶段：反向录入云端新增
    for rid, remote in remote_data.items():
        if rid in processed_remote_rids:
            continue

        print(f"★ 发现云端新物品: {remote['name']}")
        new_lid = remote["local_id"] or f"item-lark-{uuid.uuid4().hex[:8]}"
        if not remote["local_id"]:
            subprocess.run([LARK_CLI, "base", "+record-upsert", "--base-token", BASE_TOKEN, "--table-id", TABLE_ID, "--record-id", rid, "--json", json.dumps({"本地数据库ID": new_lid}, ensure_ascii=False)])

        # 拉取关联字段的 record_id
        remote_cat_rids = extract_link_record_id(remote.get("category_link"))
        cat_rid = remote_cat_rids[0] if remote_cat_rids else None

        new_item = {
            "id": new_lid,
            "name": remote["name"],
            "category": normalize_select(remote["category"]),
            "sub_category": remote["sub_category"],
            "category_record_id": cat_rid,
            "location": remote["location"],
            "container": remote["container"],
            "remark": remote["remark"],
            "status": normalize_select(remote["status"]) or "active",
            "updated_at": datetime.now().isoformat(),
            "feishu_record_id": rid,
        }
        local_items.append(new_item)
        new_local_count += 1

    # 最终清理与保存
    unique_items = []
    seen_ids = set()
    for it in local_items:
        if it["id"] not in seen_ids:
            unique_items.append(it)
            seen_ids.add(it["id"])
    items_data["items"] = unique_items

    with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(items_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 同步完成！推送 {push_count}，拉取 {pull_count}，跳过内容未变项 {skip_count}，新增录入 {new_local_count}。")


if __name__ == "__main__":
    sync()
