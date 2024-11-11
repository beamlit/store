import json
import os
from typing import Dict, List

import yaml


def parse_beamlit_yaml() -> List[Dict]:
    """Parse the beamlit.yaml file to get function configurations."""
    yaml_path = os.path.join(os.path.dirname(__file__), "beamlit.yaml")

    if not os.path.exists(yaml_path):
        raise Exception("beamlit.yaml not found")

    with open(yaml_path, "r") as f:
        config = yaml.safe_load(f)

    for key in os.environ:
        if key.startswith("BL_"):
            if key == "BL_FUNCTIONS":
                config['functions'] = os.getenv(key).split(',')
            elif key == "BL_CHAIN":
                config['chain'] = json.loads(os.getenv(key))
            else:
                config[key.replace("BL_", "").lower()] = os.getenv(key)

    if os.getenv("BL_CREDENTIALS") and config.get('api_key') is None:
        config['api_key'] = os.environ["BL_CREDENTIALS"]

    config['environment'] = config.get('environment', 'production')
    config['base_url'] = config.get('base_url', "https://api.beamlit.dev/v0")
    config['run_url'] = config.get('run_url', "https://run.beamlit.dev")
    return config