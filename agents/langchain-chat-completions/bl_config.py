import json
import os
from typing import Dict, List

import yaml

global BL_CONFIG
BL_CONFIG = {}

def init() -> List[Dict]:
    """Parse the beamlit.yaml file to get function configurations."""
    global BL_CONFIG
    yaml_path = os.path.join(os.path.dirname(__file__), "beamlit.yaml")

    if not os.path.exists(yaml_path):
        raise Exception("beamlit.yaml not found")

    with open(yaml_path, "r") as f:
        BL_CONFIG = yaml.safe_load(f)

    for key in os.environ:
        if key.startswith("BL_"):
            if key == "BL_FUNCTIONS":
                BL_CONFIG['functions'] = os.getenv(key).split(',')
            elif key == "BL_CHAIN":
                BL_CONFIG['chain'] = json.loads(os.getenv(key))
            else:
                BL_CONFIG[key.replace("BL_", "").lower()] = os.getenv(key)

    BL_CONFIG['environment'] = BL_CONFIG.get('environment', 'production')
    BL_CONFIG['base_url'] = BL_CONFIG.get('base_url', "https://api.beamlit.dev/v0")
    BL_CONFIG['run_url'] = BL_CONFIG.get('run_url', "https://run.beamlit.dev")
    return BL_CONFIG