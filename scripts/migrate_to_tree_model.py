import json
import os

PROJECT_ROOT = "/Users/robinlu/Self-established_skill/home-organizer"
OLD_MAP_FILE = os.path.join(PROJECT_ROOT, "data", "space_map.json")
NEW_MAP_FILE = os.path.join(PROJECT_ROOT, "data", "space_tree.json")

def migrate():
    with open(OLD_MAP_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    spaces = data.get('spaces', [])
    new_records = []
    
    for s in spaces:
        if 'containers' in s:
            room_id = s.get('name') 
            new_records.append({
                "id": room_id,
                "name": s.get('name'),
                "parent_id": None,
                "type": s.get('type', 'room'),
                "frequency": s.get('frequency', ''),
                "status": s.get('status', ''),
                "primary_activity": s.get('primary_activity', ''),
                "notes": s.get('description') or s.get('notes', '') # 修改为 notes 或者保留为 description
            })
            for c in s['containers']:
                c_id = f"{room_id}_{c.get('name')}"
                new_records.append({
                    "id": c_id,
                    "name": c.get('name'),
                    "parent_id": room_id,
                    "type": c.get('type', 'container'),
                    "frequency": c.get('frequency', ''),
                    "status": c.get('status', ''),
                    "primary_activity": c.get('primary_activity', ''),
                    "notes": c.get('description') or c.get('notes', '')
                })
        else:
            new_records.append({
                "id": s.get('id') or s.get('name'),
                "name": s.get('name'),
                "parent_id": s.get('parent'),
                "type": s.get('type', 'unspecified'),
                "frequency": s.get('frequency', ''),
                "status": s.get('status', ''),
                "primary_activity": s.get('primary_activity', ''),
                "notes": s.get('description') or s.get('notes', '') # 统一使用 notes 字段
            })
            
    name_to_id = {r['name']: r['id'] for r in new_records if r.get('name') and r.get('id')}
    
    for r in new_records:
        parent_val = r.get('parent_id')
        if parent_val:
            if parent_val not in [rec['id'] for rec in new_records]:
                if parent_val in name_to_id:
                    r['parent_id'] = name_to_id[parent_val]
                else:
                    new_parent_id = f"virtual_{parent_val}"
                    name_to_id[parent_val] = new_parent_id
                    r['parent_id'] = new_parent_id
                    new_records.append({
                        "id": new_parent_id,
                        "name": parent_val,
                        "parent_id": None,
                        "type": "room", 
                        "frequency": "",
                        "status": "",
                        "primary_activity": "",
                        "notes": "系统自动生成的缺失父节点"
                    })
    
    output = {
        "nodes": new_records
    }
    
    with open(NEW_MAP_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        
    print(f"✅ 转换完成，已添加 notes(备注) 字段。")

if __name__ == '__main__':
    migrate()
