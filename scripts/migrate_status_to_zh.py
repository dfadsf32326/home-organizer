import json
import os

PROJECT_ROOT = "/Users/robinlu/Self-established_skill/home-organizer"
ITEMS_FILE = os.path.join(PROJECT_ROOT, "data/items.json")

STATUS_MAP = {
    "active": "正常",
    "deleted": "已丢弃",
    "pending": "待定/未分类",
    "suspected_broken": "疑似损坏",
    "For Sale": "待售出",
    "sold": "已售出",
    "lost": "遗失"
}

def main():
    with open(ITEMS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    items = data.get("items", [])
    count = 0
    
    for item in items:
        old_status = item.get("status")
        if old_status in STATUS_MAP:
            item["status"] = STATUS_MAP[old_status]
            count += 1
            print(f"转换: {old_status} -> {item['status']} ({item.get('name')})")
            
    with open(ITEMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"\n✅ 成功将 {count} 个物品的状态转换为中文！")

if __name__ == "__main__":
    main()
