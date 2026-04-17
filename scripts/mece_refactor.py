import json

json_path = '/Users/robinlu/.workbuddy/skills/home-organizer/data/items.json'

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

items = data.get('items', [])

# 定义 MECE 顶层分类映射逻辑
def map_to_mece(item):
    main_cat = item['category'][0]
    mid_cat = item['category'][1]
    sub_cat = item['category'][2]
    content = item['content'].lower()
    
    # 特殊保留原则：血糖管理对老板极其重要，保留为独立中类
    if "血糖" in mid_cat or "胰岛素" in content or "血糖" in content:
        return ["1. 电子与电气设备", "血糖管理", sub_cat]

    # 1. 电子与电气设备 (依靠电力驱动)
    if any(word in main_cat for word in ["电子设备", "电器"]) or \
       any(word in mid_cat for word in ["网络", "存储", "交互", "移动设备", "电视", "电器", "测量设备"]) or \
       any(word in content for word in ["电脑", "手机", "充电", "电池", "灯", "泵", "仪"]):
        return ["1. 电子与电气设备", mid_cat or "其他设备", sub_cat]

    # 4. 织物与服饰 (物理属性优先)
    if "织物" in main_cat or any(word in mid_cat for word in ["服装", "床上", "卫浴"]):
        return ["4. 织物与服饰", mid_cat, sub_cat]

    # 3. 消耗品与化成品 (使用后消失)
    if any(word in main_cat for word in ["化成品", "消耗品", "医疗与专业耗材"]) or \
       any(word in mid_cat for word in ["食品", "护理", "清洁", "药物", "耗材", "试纸"]):
        return ["3. 消耗品与化成品", mid_cat, sub_cat]

    # 5. 信息与资产
    if "信息" in main_cat or "印刷品" in mid_cat or any(word in sub_cat for word in ["书籍", "证件", "合同", "病历"]):
        return ["5. 信息与资产", mid_cat or "文档/书籍", sub_cat]

    # 2. 工具与耐用品 (非电力，长期使用)
    if "工具" in main_cat or "容器" in main_cat or \
       any(word in mid_cat for word in ["手动工具", "饮用容器", "储存容器", "收纳"]):
        return ["2. 工具与耐用品", mid_cat, sub_cat]

    # 6. 杂项与特殊品
    return ["6. 杂项与特殊品", mid_cat or "其他", sub_cat]

# 执行改造
new_items = []
for item in items:
    new_cat = map_to_mece(item)
    item['category'] = new_cat
    new_items.append(item)

data['items'] = new_items
data['version'] = "1.2 (MECE Refactored)"

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Successfully refactored {len(new_items)} items to MECE structure.")
