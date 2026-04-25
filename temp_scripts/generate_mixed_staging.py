import json
import os

with open("data/space_tree.json", "r", encoding="utf-8") as f:
    spaces = json.load(f).get("nodes", [])

space_map = {s["name"]: s.get("record_id") for s in spaces}
space_family_id = space_map.get("家人病历袋")
space_insurance_id = space_map.get("保险合同袋子")

with open("data/category_mapping.json", "r", encoding="utf-8") as f:
    cats = json.load(f)

cat_health = cats.get("健康档案", {})
cat_finance = cats.get("财务与合同", {})

staging = []

# 1. 家人病历袋 -> 健康档案
medical_items = ["外公的病历", "妈妈的病历", "爸爸的病历", "奶奶的病历"]
for item in medical_items:
    staging.append({
        "name": item,
        "category": cat_health.get("major"),
        "sub_category": "健康档案",
        "category_record_id": cat_health.get("record_id"),
        "space_record_id": space_family_id,
        "location": "暂存区",
        "container": "家人病历袋",
        "id": None,
        "quantity": 1,
        "status": ["盘点中"]
    })

# 2. 晶体植入的盒子 -> 作为独立物品，但分类不明，默认归为 "收纳工具" 之类的，根据要求此处仅作为物品存储，即暂不作为独立物品推入items，因为用户之前也提到“这个作为物品储存”，说明它是容器，但没有任何挂载物品说明？
# 修正理解：用户说“有一个晶体植入的盒子，这个作为物品储存”是指它也是个被盘点的【物品】本身？还是【容器】？结合上下文和上次刚建了空间，它是个被储存的物品（或者空容器入库作为物品），这里将其作为“物品”放入暂存。
staging.append({
    "name": "晶体植入的盒子",
    "category": "🏠 家居与工具",  # 假设归类为收纳工具
    "sub_category": "生活用品",   # 临时归类
    "category_record_id": cats.get("生活用品", {}).get("record_id"),
    "space_record_id": None, 
    "location": "未分配",
    "container": "无",
    "id": None,
    "quantity": 1,
    "status": ["盘点中"]
})

# 3. 保险合同袋子 -> 财务与合同
insurance_items = [
    "爸爸的国寿宏泰年金保险分红型合同",
    "爸爸的金佑人生保险合同",
    "爸爸的第二份金佑人身保险合同",
    "爸爸的长相伴保险合同",
    "爸爸的爱加满合同",
    "爸爸的爱无忧保险合同",
    "我的金佑人生保险合同",
    "我的另一份金佑人生保险合同",
    "爸爸的金佑人生保险合同",
    "爸爸的安行保保险合同"
]

for item in insurance_items:
    staging.append({
        "name": item,
        "category": cat_finance.get("major"),
        "sub_category": "财务与合同",
        "category_record_id": cat_finance.get("record_id"),
        "space_record_id": space_insurance_id,
        "location": "暂存区",
        "container": "保险合同袋子",
        "id": None,
        "quantity": 1,
        "status": ["盘点中"]
    })

os.makedirs("data/staging", exist_ok=True)
with open("data/staging/staging_items.json", "w", encoding="utf-8") as f:
    json.dump({"items": staging}, f, ensure_ascii=False, indent=2)

print("==== 待推送盘点清单 ====")

grouped_by_container = {}
for i in staging:
    c = i["container"]
    if c not in grouped_by_container:
        grouped_by_container[c] = []
    grouped_by_container[c].append(i)

for c, items in grouped_by_container.items():
    print(f"\n📦 【所在容器：{c}】")
    for item in items:
        print(f" - [{item['sub_category']}] {item['name']} (x{item['quantity']})")

print("\n========================")

