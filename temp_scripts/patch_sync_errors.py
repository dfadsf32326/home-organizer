with open("scripts/sync_spaces_bidirectional.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    new_lines.append(line)
    if "res = subprocess.run(cmd, capture_output=True, text=True)" in line:
        new_lines.append(line.replace("res = subprocess.run", "            if res.returncode != 0:\\n                print(f\"\\n❌ 创建空间失败: {res.stderr}\\n\")\\n").replace("            if res", "        "))
        
with open("scripts/sync_spaces_bidirectional.py", "w") as f:
    # we will do it manually via file_patch
    pass
