import json
import os
import subprocess
from datetime import datetime
import uuid

# 1. 构造一条带"测试"标签的本地测试数据
test_item = {
    "id": f"test_{uuid.uuid4().hex[:8]}",
    "name": "测试专用-护手霜",
    "sub_category": "身体洗护",
    "category_record_id": "recvhlcRUjNcMt",  # 从 mapping 里查的
    "location": "次卧",
    "container": "次卧-桌子-数据线充电器盒子",  # 放进我们刚建的层级测试容器里
    "remark": "这是一条用于测试的新增记录，包含测试标签，阅后可删。",
    "status": "pending",
    "tags": ["测试"],
    "created_at": datetime.now().isoformat(),
    "updated_at": datetime.now().isoformat()
}

# 2. 读取当前的 items.json
data_file = "/Users/robinlu/Self-established_skill/home-organizer/data/items.json"
with open(data_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# 3. 将测试数据追加进去
data["items"].append(test_item)

# 4. 存回文件
with open(data_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ 成功将测试数据写入 items.json! (ID: {test_item['id']})")
print("接下来你可以运行 python scripts/sync_final.py 将其推送到飞书。")
