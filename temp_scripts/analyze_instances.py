import json
import os
from collections import defaultdict

ITEMS_FILE = os.path.expanduser("~/.hermes/skills/custom/home-organizer/data/items.json")

with open(ITEMS_FILE, "r", encoding="utf-8") as f:
    items_data = json.load(f)
    # Handle both list and dict formats safely
    items = items_data if isinstance(items_data, list) else items_data.get("items", [])

# Collect items by sub_category
category_items = defaultdict(list)
for item in items:
    sub_cat = item.get("sub_category")
    name = item.get("name")
    if sub_cat and name:
        category_items[sub_cat].append(name)

# Print unique/sample items per sub_category
for sub_cat, names in sorted(category_items.items()):
    # Get distinct names, clean up sizes/quantities for better grouping if possible, but raw is fine
    unique_names = list(set(names))
    # Pick up to 5 representative items (shortest names usually better represent the category)
    unique_names.sort(key=len)
    samples = unique_names[:8]
    print(f"* {sub_cat}: {', '.join(samples)}")
