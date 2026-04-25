#!/usr/bin/env python3
import json
import os
import argparse

def main():
    parser = argparse.ArgumentParser(description="搜索本地收纳物品")
    parser.add_argument("keyword", help="物品名称的搜索关键字")
    args = parser.parse_args()

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    items_file = os.path.join(project_root, "data", "items.json")

    if not os.path.exists(items_file):
        print(f"❌ 错误: 找不到文件 {items_file}，请先执行拉取同步。")
        return

    try:
        with open(items_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 错误: 读取 JSON 失败 ({e})")
        return

    items = data.get("items", [])
    found_count = 0
    
    print(f"🔍 正在搜索 '{args.keyword}'...\n")
    
    for item in items:
        name = item.get("name", "")
        if args.keyword.lower() in name.lower():
            found_count += 1
            print(f"📦 物品: {name}")
            print(f"  ├─ 📍 存放位置: {item.get('location') or '未知'}")
            print(f"  ├─ 🗃️ 存放容器: {item.get('container') or '未知'}")
            status = item.get("status")
            if status:
                print(f"  └─ 🏷️ 状态: {status}")
            else:
                print(f"  └─ 🏷️ 状态: 正常")
            print()

    if found_count == 0:
        print(f"🥺 未找到包含关键字 '{args.keyword}' 的物品。")
    else:
        print(f"✅ 共找到 {found_count} 个相关物品。")

if __name__ == "__main__":
    main()
