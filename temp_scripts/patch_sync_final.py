import json

path = "/Users/robinlu/.hermes/skills/home-organizer/scripts/sync_final.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

# Fix the LARK_BASE_TOKEN issue properly in the script
old_str = 'BASE_TOKEN="PS56bP...OnJb"'
new_str = 'import os\nBASE_TOKEN=os.environ.get("LARK_BASE_TOKEN")'

if old_str in code:
    code = code.replace(old_str, new_str)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    print("Patch applied to sync_final.py.")
else:
    print("String not found in sync_final.py!")

