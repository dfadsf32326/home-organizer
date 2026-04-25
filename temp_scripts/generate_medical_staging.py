import json
import os

items = [
    "2023年10月11日四川省人民医院病历和检查",
    "成都华夏眼科医院晶体植入手术复查卡",
    "2021年7月7日成都市第二人民医院体检报告",
    "2022年6月12日环亚体检报告",
    "2021年10月3日成都心理相关检查报告",
    "2021年10月3日成都棕南医院焦虑自评表",
    "2021年10月3日成都棕南医院抑郁自评表",
    "2021年10月3日成都棕南医院匹兹堡睡眠质量测评表",
    "2023年3月16日华西近红外脑功能检测报告",
    "心理评估检测报告",
    "2023年5月14日市一医院眼睛检测报告",
    "2020年5月24日眼球地图检测报告",
    "其他各种病历和检测报告(待电子化)"
]

staging = []
for i in items:
    staging.append({
        "name": i,
        "category": "📚 文档资产",
        "sub_category": "健康档案",
        "category_record_id": "recvhlcVwfRHcp",
        "space_record_id": "recvhN14HPrYMU",
        "location": "暂存区",
        "container": "病历相关文件袋",
        "id": None,
        "quantity": 1,
        "status": ["盘点中"]
    })

os.makedirs("data/staging", exist_ok=True)
with open("data/staging/staging_items.json", "w", encoding="utf-8") as f:
    json.dump({"items": staging}, f, ensure_ascii=False, indent=2)

