import json

with open("data/space_tree.json", "r") as f:
    spaces = json.load(f)

for s in spaces:
    if s.get("name") in ["家人病历袋", "保险合同袋子"] and not s.get("record_id"):
        # We need to drop "record_id" if it exists, but it doesn't.
        # But sync_spaces_bidirectional checks if "record_id" is absent, it pushes.
        # Wait, if they were pushed, they should have been pulled?
        pass
