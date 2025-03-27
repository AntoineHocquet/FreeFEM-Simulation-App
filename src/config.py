import json
import os

def load_config():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(root, "params.json")
    with open(config_path, "r") as f:
        config = json.load(f)
    return config

