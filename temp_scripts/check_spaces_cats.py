import json

with open("data/space_tree.json", "r", encoding="utf-8") as f:
    spaces = json.load(f).get("nodes", [])

space_names = [s.get("name") for s in spaces]
print("现有相关空间:")
for n in ["家人病历袋", "保险合同袋子", "晶体植入的盒子"]:
    print(f" - {n}: {'✅ 存在' if n in space_names else '❌ 不存在'}")

with open("data/category_mapping.json", "r", encoding="utf-8") as f:
    cats = json.load(f)

print("\n现有相关分类:")
for c in ["健康档案", "财务与合同"]:
    print(f" - {c}: {'✅ 存在' if c in cats else '❌ 不存在'}")
