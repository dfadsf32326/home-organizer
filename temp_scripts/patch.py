import json

path = "/Users/robinlu/.hermes/skills/home-organizer/scripts/sync_category_mapping.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

# 将纯文本赋值修改为列表格式，以适配多选字段
old_str = 'F("sub_class"): sub_name,'
new_str = 'F("sub_class"): [sub_name],'

if old_str in code:
    code = code.replace(old_str, new_str)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    print("Patch applied successfully.")
else:
    print("String not found!")
