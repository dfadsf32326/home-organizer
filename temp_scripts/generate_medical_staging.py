import json
import os

items_to_add = [
    "2023年10月11日四川省人民医院病历和检查",
    "成都华夏眼科医院晶体植入手术复查卡",
    "2021年7月7日成都市第二人民医院体检报告",
    "2022年6月12日环亚体检报告",
    "2021年10月3日成都心理相关检查报告",
    "2021年10月3日成都棕南医院焦虑自评表",
    "2021年10月3日成都棕南医院抑郁自评表",
    "2021年10月3日成都棕南医院匹兹堡睡眠质量测评表",
    "2023年3月16日华西脑功能检测与精神调控中心近红外脑外功能检测报告",
    "心理评估检测报告",
    "成都市第一人民医院2023年5月14日眼睛检测报
...[Truncated]...
": "病历相关文件袋",
      "id": None,
      "quantity": 1,
      "status": ["盘点中"]
    })

output_data = {"items": staging_items}

os.makedirs("data/staging", exist_ok=True)
with open("data/staging/staging_items.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print("✅ 病历档案暂存数据生成成功！")
