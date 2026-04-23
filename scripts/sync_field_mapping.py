#!/usr/bin/env python3
import json
import subprocess
import os

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
BASE_TOKEN = "PS56bPhyNaWXRdsJX78cxyIOnJb"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIELD_MAPPING_FILE = os.path.join(PROJECT_ROOT, "data", "field_mapping.json")

def main():
    print("开始同步字段映射表 (field_mapping.json)...")
    
    if not os.path.exists(FIELD_MAPPING_FILE):
        print(f"❌ 找不到文件: {FIELD_MAPPING_FILE}")
        return
        
    with open(FIELD_MAPPING_FILE, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
        
    tables = mapping.get("tables", {})
    changed_total = 0
    
    for table_key, table_info in tables.items():
        table_id = table_info.get("table_id")
        if not table_id:
            continue
            
        print(f"\n正在拉取表 [{table_key}] (ID: {table_id}) 的最新字段信息...")
        # limit 1 即可，我们只需要外层的 field_id_list 和 fields 元数据
        cmd = [LARK_CLI, "base", "+record-list", "--base-token", BASE_TOKEN, "--table-id", table_id, "--limit", "1"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        
        if res.returncode != 0:
            print(f"⚠️ 拉取表 {table_key} 失败，跳过。错误: {res.stderr}")
            continue
            
        try:
            data_full = json.loads(res.stdout)
            data = data_full.get("data", {})
            field_ids = data.get("field_id_list", [])
            field_names = data.get("fields", [])
            
            if len(field_ids) != len(field_names):
                print(f"⚠️ 表 {table_key} 的字段 ID 和名称数量不匹配，跳过。")
                continue
                
            # 构建最新的 字段ID -> 字段名 映射
            remote_fields_map = dict(zip(field_ids, field_names))
            
            # 更新本地 mapping
            local_fields = table_info.get("fields", {})
            for local_key, field_props in local_fields.items():
                fid = field_props.get("feishu_id")
                old_name = field_props.get("feishu_name")
                
                if fid in remote_fields_map:
                    new_name = remote_fields_map[fid]
                    if new_name != old_name:
                        print(f"  🔄 发现名称变更: 本地键 [{local_key}] 的飞书显示名 '{old_name}' -> '{new_name}'")
                        field_props["feishu_name"] = new_name
                        changed_total += 1
                else:
                    print(f"  ⚠️ 警告: 字段 [{local_key}] (ID: {fid}) 在飞书中不存在，可能已被删除！")
        except Exception as e:
            print(f"❌ 解析表 {table_key} 数据出错: {e}")
            
    if changed_total > 0:
        with open(FIELD_MAPPING_FILE, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        print(f"\n🎉 同步完成！共自动更新了 {changed_total} 个字段名称，已保存至 field_mapping.json。")
    else:
        print("\n✅ 同步完成！所有字段名称均已是最新，无变化。")

if __name__ == '__main__':
    main()
