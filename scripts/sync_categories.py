#!/usr/bin/env python3
"""
分类表同步 - 便捷入口（兼容旧调用方式）
默认执行双向同步，等同于 python sync_category_mapping.py --sync
"""

import subprocess
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NEW_SCRIPT = os.path.join(SCRIPT_DIR, "sync_category_mapping.py")

if __name__ == "__main__":
    # 如果带了参数就透传，否则默认 --sync
    args = sys.argv[1:] if len(sys.argv) > 1 else ["--sync"]
    subprocess.run([sys.executable, NEW_SCRIPT] + args)
