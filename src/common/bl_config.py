import json
import os
from logging import getLogger
from typing import Dict, List

import requests
import yaml

global BL_CONFIG
BL_CONFIG = {}

def init_agent():
    from common.bl_generate import generate

    logger = getLogger(__name__)

    # Init configuration from environment variables
    if BL_CONFIG.get("agent_functions") or BL_CONFIG.get("agent_chain"):
        if BL_CONFIG.get("agent_functions"):
            BL_CONFIG['agent_functions'] = json.loads(BL_CONFIG["agent_functions"])
        else:
            BL_CONFIG['agent_functions'] = []
        if BL_CONFIG.get("agent_chain"):
            BL_CONFIG['agent_chain'] = json.loads(BL_CONFIG["agent_chain"])
        else:
            BL_CONFIG['agent_chain'] = []
        return

    # Init configuration from beamlit control plane
    name = BL_CONFIG['name']
    env = BL_CONFIG['environment']
    headers = {"X-Beamlit-Workspace": BL_CONFIG['workspace'], "X-Beamlit-Environment": env}

    if BL_CONFIG.get('api_key'):
        headers["Api-Key"] = BL_CONFIG['api_key']
    elif BL_CONFIG.get('jwt'):
        headers["X-Beamlit-Authorization"] = f"Bearer {BL_CONFIG['jwt']}"

    response = requests.get(f"{BL_CONFIG['base_url']}/agents/{name}/deployments/{env}", headers=headers, params={"configuration": "true"})
    response.raise_for_status()
    agent_config = response.json()
    BL_CONFIG['agent_functions'] = agent_config['functions']
    BL_CONFIG['agent_chain'] = agent_config['agent_chain']


    destination = f"{os.path.dirname(__file__)}/../agents/beamlit.py"


    content_generate = generate(destination, dry_run=True)
    compared_content = None
    if os.path.exists(destination):
        compared_content = open(destination, "r").read()

    if not os.path.exists(destination) or (compared_content and content_generate != compared_content):
        logger.info("Generating agent code")
        generate(destination)

def init(directory: str = os.path.dirname(__file__)) -> List[Dict]:
    """Parse the beamlit.yaml file to get configurations."""
    global BL_CONFIG
    yaml_path = os.path.join(directory, "beamlit.yaml")

    if os.path.exists(yaml_path):
        with open(yaml_path, "r") as f:
            BL_CONFIG = yaml.safe_load(f)

    for key in os.environ:
        if key.startswith("BL_"):
            BL_CONFIG[key.replace("BL_", "").lower()] = os.getenv(key)

    BL_CONFIG['name'] = BL_CONFIG.get('name', 'dev-name')
    BL_CONFIG['environment'] = BL_CONFIG.get('environment', 'production')
    BL_CONFIG['base_url'] = BL_CONFIG.get('base_url', "https://api.beamlit.dev/v0")
    BL_CONFIG['run_url'] = BL_CONFIG.get('run_url', "https://run.beamlit.dev")
    BL_CONFIG['workspace'] = BL_CONFIG.get('workspace')
    BL_CONFIG['type'] = BL_CONFIG.get('type')

    if not BL_CONFIG['workspace']:
        raise Exception("Workspace is required")
    if not BL_CONFIG['environment']:
        raise Exception("Environment is required")
    if not BL_CONFIG['name']:
        raise Exception("Name is required")
    if not BL_CONFIG['type']:
        raise Exception("Type is required")
    return BL_CONFIG
