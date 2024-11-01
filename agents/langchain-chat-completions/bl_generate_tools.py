import json
import os
from typing import Dict, List

import requests
import yaml

BEAMLIT_API_KEY = os.getenv("BEAMLIT_API_KEY")
BEAMLIT_JWT = os.getenv("BEAMLIT_JWT")
BEAMLIT_WORKSPACE = os.getenv("BEAMLIT_WORKSPACE")
BEAMLIT_BASE_URL = os.getenv("BEAMLIT_BASE_URL", "https://api.beamlit.dev/v0")
BEAMLIT_RUN_URL = os.getenv("BEAMLIT_RUN_URL", "https://run.beamlit.dev")
BEAMLIT_TOOLS = os.getenv("BEAMLIT_TOOLS", "search-zag,math-zag")
try:
    BEAMLIT_CHAIN = json.loads(os.getenv("BEAMLIT_CHAIN", None))
except:
    BEAMLIT_CHAIN = None

def parse_beamlit_yaml() -> List[Dict]:
    """Parse the beamlit.yaml file to get tool configurations."""
    yaml_path = os.path.join(os.path.dirname(__file__), "beamlit.yaml")

    if not os.path.exists(yaml_path):
        raise Exception("beamlit.yaml not found")

    with open(yaml_path, "r") as f:
        config = yaml.safe_load(f)
    config['tools'] = config.get('tools', BEAMLIT_TOOLS.split(','))
    config['api_key'] = config.get('api_key', BEAMLIT_API_KEY)
    config['jwt'] = config.get('jwt', BEAMLIT_JWT)
    config['workspace'] = config.get('workspace', BEAMLIT_WORKSPACE)
    config['base_url'] = config.get('base_url', BEAMLIT_BASE_URL)
    config['chain'] = config.get('chain', BEAMLIT_CHAIN)
    return config

def get_tools_from_beamlit(beamlit_config: Dict) -> List[Dict]:
    headers = {"Api-Key": beamlit_config['api_key'], "X-Beamlit-Workspace": beamlit_config['workspace']}
    response = requests.get(f"{beamlit_config['base_url']}/tools", headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to get tools from beamlit: {response.text}")
    tools = response.json()
    for name in beamlit_config['tools']:
        if not any(tool['name'] == name for tool in tools):
            raise Exception(f"Tool {name} not found in beamlit")
    return [tool for tool in tools if tool['name'] in beamlit_config['tools']]

def generate_tool_code(beamlit_config: Dict, tool_config: Dict) -> str:
    name = tool_config["name"].title().replace("-", "")
    args_list = ", ".join(f"{param['name']}: str" for param in tool_config["parameters"])
    args_schema = "\n    ".join(
        f"{param['name']}: str = Field(description='{param.get('description', '')}')"
        for param in tool_config["parameters"]
    )
    return_direct = str(tool_config.get("return_direct", False))
    if beamlit_config.get('jwt'):
        headers = f'''{{
                "Authorization": "Bearer {beamlit_config['jwt']}"
            }}'''
    else:
        headers = f'''{{
                "Api-Key": "{beamlit_config['api_key']}"
            }}'''
    return f'''
class Beamlit{name}Input(BaseModel):
    {args_schema}

class Beamlit{name}(BaseTool):
    name: str = "beamlit_{tool_config['name'].replace("-", "_")}"
    description: str = """{tool_config['description']}"""
    args_schema: Type[BaseModel] = Beamlit{name}Input

    response_format: Literal["content_and_artifact"] = "content_and_artifact"
    return_direct: bool = {return_direct}

    def _run(
        self,
        {args_list},
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Tuple[Union[List[Dict[str, str]], str], Dict]:
        try:
            headers = {headers}
            response = requests.post("{BEAMLIT_RUN_URL}/{tool_config['workspace']}/tools/{tool_config['name']}", headers=headers, json={{{", ".join(f'"{param['name']}": {param['name']}' for param in tool_config["parameters"])}}})
            return response.json(), {{}}
        except Exception as e:
            return repr(e), {{}}
'''

def generate_chain_code(beamlit_config: Dict, tools: List[Dict]) -> str:
    chain = beamlit_config['chain']
    return f'''
class BeamlitChain(BaseTool):
    name: str = "{chain['name']}"
    description: str = """{chain['description']}"""
    args_schema: Type[BaseModel] = BeamlitMathZagInput

    response_format: Literal["content_and_artifact"] = "content_and_artifact"
    return_direct: bool = False

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Tuple[Union[List[Dict[str, str]], str], Dict]:
        return f"From your query: {{query}}, I ordered a burger", {{}}
'''

def generate_tools(destination: str, beamlit_config: Dict, tools: List[Dict]):
    imports = '''from typing import Dict, List, Literal, Optional, Tuple, Type, Union
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import requests
'''

    export_code = '\n\ntools = ['
    code = imports
    for tool_config in tools:
        code += generate_tool_code(beamlit_config, tool_config)
        export_code += f'Beamlit{tool_config["name"].title().replace("-", "")}(),'
    if beamlit_config.get('chain') and beamlit_config['chain'].get('enabled'):
        code += generate_chain_code(beamlit_config, tools)
    export_code = export_code[:-1]
    export_code += ']'
    with open(destination, "w") as f:
        f.write(code + export_code)

def run(destination: str):
    beamlit_config = parse_beamlit_yaml()
    tools = get_tools_from_beamlit(beamlit_config)
    generate_tools(destination, beamlit_config, tools)