import json

try:
    with open("data/items.json", "r", encoding="utf-8") as f:
        items = json.load(f)
        
    for item in items:
        space = item.get("space")
        if space in ["家人病历袋", "保险合同袋子"]:
            print(f"[{space}] {item.get('name')}")
except Exception as e:
    print(e)
