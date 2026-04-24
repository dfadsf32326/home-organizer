import os
path = "/Users/robinlu/.hermes/skills/custom/home-organizer/scripts/sync_spaces_bidirectional.py"
content = open(path).read()
lines = content.split('\n')
for i, line in enumerate(lines):
    if "BASE_TOKEN = " in line:
        lines[i] = 'BASE_TOKEN="PS56bPNKtaH7GjsM9LfcBfJOnJb"'
open(path, 'w').write('\n'.join(lines))
