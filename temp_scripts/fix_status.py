import json
from datetime import datetime

path = "/Users/robinlu/.hermes/skills/home-organizer/data/items.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

NOW = datetime.now().isoformat()
count = 0

for item in data.get("items", []):
    changed = False
    
    # 修复写成英文的状态
    if item.get("status") == "pending":
        item["status"] = "正常"  # 标准库存状态
        changed = True
        
    # 清理多余的、不符合中文字典规范的非法字段
    if "lifecycle_status" in item:
        del item["lifecycle_status"]
        changed = True
        
    if changed:
        item["updated_at"] = NOW
        count += 1

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Fixed {count} items.")
