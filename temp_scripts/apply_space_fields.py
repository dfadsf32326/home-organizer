import re

with open("scripts/sync_spaces_bidirectional.py", "r") as f:
    code = f.read()

code = code.replace('"type": "fld1m8v2Nq",', '"type": "flddMrA84a",')

with open("scripts/sync_spaces_bidirectional.py", "w") as f:
    f.write(code)

print("Updated field mapping.")
