import csv
import json
import os

csv_path = '/Users/robinlu/Downloads/整理收纳 - 1.csv'
json_path = '/Users/robinlu/.workbuddy/skills/home-organizer/data/items.json'

items_data = []
spaces_map = {}

with open(csv_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Skip empty rows or header-only rows
        if not any(row.values()):
            continue
            
        main_cat = row.get('大类（层级 1：宏观本质）', '').strip()
        mid_cat = row.get('中类（层级 2：结构/功能亚型）', '').strip()
        sub_cat = row.get('小类（层级 3：具体属性/用途细分）', '').strip()
        item_list = row.get('物品清单（穷尽式）', '').strip()
        is_stored = row.get('是否收纳', '').strip()
        container = row.get('容器', '').strip()
        location = row.get('位置', '').strip()
        
        if not item_list and not main_cat:
            continue

        # Add to items
        items_data.append({
            "category": [main_cat, mid_cat, sub_cat],
            "content": item_list,
            "is_stored": is_stored == '是',
            "container": container,
            "location": location
        })

        # Track spaces and sub_units
        if location:
            if location not in spaces_map:
                spaces_map[location] = set()
            if container:
                spaces_map[location].add(container)

# Build the spaces structure
final_spaces = []
for loc, containers in spaces_map.items():
    final_spaces.append({
        "id": loc.lower().replace(" ", "-"),
        "name": loc,
        "status": "pending",
        "sub_units": [{"id": c.lower().replace(" ", "-"), "name": c, "status": "pending"} for c in containers if c]
    })

# Merge with existing bedroom units defined by user
bedroom_units = [
    {"id": "desk", "name": "桌子", "status": "pending"},
    {"id": "bed", "name": "床", "status": "pending"},
    {"id": "wardrobe-drawers", "name": "衣柜抽屉", "status": "pending"},
    {"id": "wardrobe-hanging-rod", "name": "衣柜左上挂杆", "status": "pending"},
    {"id": "wardrobe-bottom-space", "name": "衣柜左下空间", "status": "pending"}
]

# Check if bedroom exists in final_spaces, if not add it, if yes merge sub_units
bedroom_found = False
for space in final_spaces:
    if space["name"] == "卧室":
        existing_ids = [u["id"] for u in space["sub_units"]]
        for bu in bedroom_units:
            if bu["id"] not in existing_ids:
                space["sub_units"].append(bu)
        bedroom_found = True
        break

if not bedroom_found:
    final_spaces.append({
        "id": "bedroom",
        "name": "卧室",
        "status": "pending",
        "sub_units": bedroom_units
    })

final_data = {
    "version": "1.1",
    "spaces": final_spaces,
    "items": items_data
}

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2)

print(f"Successfully imported {len(items_data)} rows into {json_path}")
