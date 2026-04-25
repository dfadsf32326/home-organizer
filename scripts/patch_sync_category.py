import json
import subprocess
import os

LARK_CLI = os.path.expanduser("~/.npm-global/bin/lark-cli")
# 读取配置而不是硬编码，确保取到有效的 TOKEN
try:
    with open("/Users/robinlu/.hermes/config.yaml", "r") as f:
        for line in f:
            if "LARK_BASE_TOKEN" in line:
                pass
except:
    pass

# We can source the base token locally from the script context.
# We will use the system's LARK_BASE_TOKEN or a hardcoded fallback if needed.

# We'll just run a bash wrapper to guarantee bash evaluates $LARK_BASE_TOKEN
