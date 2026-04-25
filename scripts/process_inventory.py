import json
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STAGING_FILE = os.path.join(PROJECT_ROOT, "data/staging/staging_items.json")
# 这是一个占位用的示例，实际流程应由对话/语音触发
print("请使用 push_staging.py 直接将盘点好的数据推送到飞书。")
