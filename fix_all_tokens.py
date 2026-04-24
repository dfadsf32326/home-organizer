import os
import glob

files = glob.glob("/Users/robinlu/.hermes/skills/custom/home-organizer/scripts/*.py")

for path in files:
    content = open(path).read()
    lines = content.split('\n')
    changed = False
    for i, line in enumerate(lines):
        if line.startswith('BASE_TOKEN='):
            lines[i] = 'BASE_TOKEN=os.environ.get("LARK_BASE_TOKEN")'
            changed = True
    if changed:
        open(path, 'w').write('\n'.join(lines))
        print(f"Fixed {path}")
