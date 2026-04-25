import json
import os

def get_space_mapping(space_tree_path="data/space_tree.json"):
    """
    读取单点数据源 space_tree.json，并在内存中动态生成映射字典。
    返回:
        name_to_rid: dict, { "空间名称": "recvhXXXXX" }
        rid_to_node: dict, { "recvhXXXXX": { 完整的节点数据 } }
    """
    if not os.path.exists(space_tree_path):
        return {}, {}
        
    with open(space_tree_path, "r", encoding="utf-8") as f:
        tree_data = json.load(f)
        
    name_to_rid = {}
    rid_to_node = {}
    
    # 支持 {"version": "x.x", "data": [...]} 格式
    nodes = tree_data.get("data", []) if isinstance(tree_data, dict) else tree_data
        
    for node in nodes:
        rid = node.get("record_id")
        name = node.get("name")
        if rid:
            rid_to_node[rid] = node
            if name:
                name_to_rid[name] = rid
                
    return name_to_rid, rid_to_node
