import json
import os

# 定义 MECE 分类逻辑
def get_mece_category(item_name):
    item_name = item_name.lower()
    if any(kw in item_name for kw in ['macbook', '手机', '音响', '充电器', '线', '剃须刀', '血糖仪', '电池']):
        return ["1. 电子与电气设备", "移动设备与穿戴", "核心设备"]
    if any(kw in item_name for kw in ['香水', '卸妆油', '洁面乳', '发泥', '发胶', '止汗剂', '剃须膏', '牙膏', '牙线', '洗脸巾', '创可贴', '棉签']):
        return ["3. 消耗品与化成品", "个人护理与健康品", "护理用品"]
    if any(kw in item_name for kw in ['补剂', '维生素', '锌']):
        return ["3. 消耗品与化成品", "药物与保健品", "营养补剂"]
    if any(kw in item_name for kw in ['锅', '电磁炉', '高压锅', '蒸格']):
        return ["2. 工具与耐用品", "家用电器与设备", "烹饪设备"]
    if any(kw in item_name for kw in ['裤', '卫衣', '风衣', '外套', '书包', '行李箱', '挎包']):
        return ["4. 织物与服饰", "服装与配饰", "日常服饰"]
    if any(kw in item_name for kw in ['纸巾', '垃圾袋']):
        return ["6. 杂项与特殊品", "纸制品", "日用纸品"]
    return ["6. 杂项与特殊品", "其他", "待分类"]

# 搬家清单中的物品（从 items.md 提取）
relocation_items = [
    "大行李箱（26寸）", "小行李箱（20寸，灰色）", "书包", "搬家纸箱",
    "香奈儿香水", "电磁炉", "血糖用品包", "相机", "不锈钢锅", "蒸格", "高压锅", "卸妆油", "烫发夹子",
    "微波炉", "Insta 360 稳定器",
    "MacBook Air", "拜耳血糖仪", "身份证", "胰岛素笔", "便携挂钩秤", "充电器", "充电线",
    "指甲刀", "剪鼻毛夹子", "芦荟胶 110g", "挎包",
    "蓝牙音响", "充电器", "充电线", "MacBook", "垃圾袋", "纸巾", "补剂（锌）", "补剂（维生素D）",
    "黑色保暖裤", "灰色翻毛卫衣", "棕色优衣库风衣外套",
    "香水分装 x2", "香水空瓶", "发泥", "发胶", "止汗剂", "剃须刀更换刀头", "剃须膏", "洁面乳", "洗脸巾", "牙线", "牙膏"
]

# 加载现有 items.json
items_path = '/Users/robinlu/.workbuddy/skills/home-organizer/data/items.json'
with open(items_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

existing_contents = {item['content'] for item in data['items']}

# 转换并添加新物品
for item_name in relocation_items:
    if item_name not in existing_contents:
        new_item = {
            "category": get_mece_category(item_name),
            "content": item_name,
            "is_stored": True,
            "container": "搬家行李/待定",
            "location": "待整理区域",
            "status": "from_relocation_skill"
        }
        data['items'].append(new_item)

# 保存更新后的数据
with open(items_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"成功从搬家清单导入并重分类了 {len(relocation_items)} 项物品。")
