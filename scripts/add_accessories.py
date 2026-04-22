import json
import uuid
from datetime import datetime

ITEMS_FILE = "/Users/robinlu/.hermes/skills/home-organizer/data/items.json"
MAPPING_FILE = "/Users/robinlu/.hermes/skills/home-organizer/data/category_mapping.json"
NOW = datetime.now().isoformat()
CONTAINER = "手机电子产品配件箱"

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

items_data = load_json(ITEMS_FILE)
mapping = load_json(MAPPING_FILE)

# Helper function to get category record id
def get_cat_id(sub_cat):
    return mapping.get(sub_cat, {}).get("record_id", "")

new_items = [
    {"name": "金属钢化膜盒子 (可作为收纳盒)", "sub_category": "收纳与包袋"},
    {"name": "5倍卡手机卡袋子", "sub_category": "外设与配件"},
    {"name": "AirPods 替换耳塞 (一对)", "sub_category": "外设与配件"},
    {"name": "Apple Watch 充电转接器", "sub_category": "动力与线材"},
    {"name": "贴膜神器 (3个)", "sub_category": "外设与配件"},
    {"name": "磁吸环", "sub_category": "外设与配件"},
    {"name": "AirPods Pro 耳机套", "sub_category": "外设与配件"},
    {"name": "Type C 转 Lightning 转接头", "sub_category": "动力与线材"},
    {"name": "U盘", "sub_category": "存储媒介"},
    {"name": "小米手环 (1)", "sub_category": "核心计算设备"},
    {"name": "小米手环 (2)", "sub_category": "核心计算设备"},
    {"name": "贴膜神器 (1个)", "sub_category": "外设与配件"},
    {"name": "3.5mm 苹果原装有线耳机", "sub_category": "外设与配件"},
]

for item in new_items:
    record = {
        "id": str(uuid.uuid4()),
        "name": item["name"],
        "sub_category": item["sub_category"],
        "container_id": CONTAINER,
        "lifecycle_status": "active",
        "status": "pending",
        "quantity": 1,
        "created_at": NOW,
        "updated_at": NOW,
        "category_record_id": get_cat_id(item["sub_category"])
    }
    items_data["items"].append(record)

save_json(items_data, ITEMS_FILE)
print(f"成功添加 {len(new_items)} 个新物品。")
