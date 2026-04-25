import json
import os

with open("data/category_mapping.json", "r", encoding="utf-8") as f:
    cats = json.load(f)

def get_cat_info(minor_name):
    info = cats.get(minor_name, {})
    return info.get("major", ""), minor_name, info.get("record_id", "")

items = [
    {"name": "城院毕业纪念品", "qty": 2, "cat": "纪念与情感"},
    {"name": "去广西阿泽结婚时拍的拍立得", "qty": 1, "cat": "纪念与情感"},
    {"name": "阳朔的印章纪念卡", "qty": 1, "cat": "纪念与情感"},
    {"name": "活动公司工作证", "qty": 1, "cat": "证件与证明"},
    {"name": "街道办工作证", "qty": 1, "cat": "证件与证明"},
    {"name": "陈苑2015级软件技术一班毕业照", "qty": 1, "cat": "纪念与情感"},
    {"name": "城院汽车与信息工程学院15级毕业留影", "qty": 1, "cat": "纪念与情感"},
    {"name": "毕棚沟的留念照片", "qty": 1, "cat": "纪念与情感"},
    {"name": "一袋证件照", "qty": 1, "cat": "证件与证明"},
    {"name": "enzo 给我送的佛牌", "qty": 1, "cat": "纪念与情感"},
    {"name": "人间攻略2的手环", "qty": 1, "cat": "纪念与情感"}
]

staging = []
for item in items:
    major, minor, cat_id = get_cat_info(item["cat"])
    staging.append({
        "name": item["name"],
        "category": major,
        "sub_category": minor,
        "category_record_id": cat_id,
        "space_record_id": None,  # 无容器
        "location": "未分配",
        "container": "无",
        "id": None,
        "quantity": item["qty"],
        "status": ["盘点中"]
    })

os.makedirs("data/staging", exist_ok=True)
with open("data/staging/staging_items.json", "w", encoding="utf-8") as f:
    json.dump({"items": staging}, f, ensure_ascii=False, indent=2)

print("==== 待推送盘点清单 (无容器散件) ====")
grouped = {}
for i in staging:
    cat = i["sub_category"]
    if cat not in grouped:
        grouped[cat] = []
    grouped[cat].append(f"{i['name']} (x{i['quantity']})")

for cat, lst in grouped.items():
    print(f"**子分类：{cat}**")
    for name in lst:
        print(f" - {name}")
    print("")

print("====================================")
