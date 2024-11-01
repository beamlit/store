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
    """Parse the beamlit.yaml file to get function configurations."""
    yaml_path = os.path.join(os.path.dirname(__file__), "beamlit.yaml")

    if not os.path.exists(yaml_path):
        raise Exception("beamlit.yaml not found")

    with open(yaml_path, "r") as f:
        config = yaml.safe_load(f)
    config['functions'] = config.get('functions', BEAMLIT_TOOLS.split(','))
    config['api_key'] = config.get('api_key', BEAMLIT_API_KEY)
    config['jwt'] = config.get('jwt', BEAMLIT_JWT)
    config['workspace'] = config.get('workspace', BEAMLIT_WORKSPACE)
    config['base_url'] = config.get('base_url', BEAMLIT_BASE_URL)
    config['chain'] = config.get('chain', BEAMLIT_CHAIN)
    return config

def get_functions_from_beamlit(beamlit_config: Dict) -> List[Dict]:
    headers = {"Api-Key": beamlit_config['api_key'], "X-Beamlit-Workspace": beamlit_config['workspace']}
    response = requests.get(f"{beamlit_config['base_url']}/functions", headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to get functions from beamlit: {response.text}")
    functions = response.json()
    for name in beamlit_config['functions']:
        if not any(function['name'] == name for function in functions):
            raise Exception(f"Function {name} not found in beamlit")
    return [function for function in functions if function['name'] in beamlit_config['functions']]

def generate_function_code(beamlit_config: Dict, function_config: Dict) -> str:
    name = function_config["name"].title().replace("-", "")
    args_list = ", ".join(f"{param['name']}: str" for param in function_config["parameters"])
    args_schema = "\n    ".join(
        f"{param['name']}: str = Field(description='{param.get('description', '')}')"
        for param in function_config["parameters"]
    )
    return_direct = str(function_config.get("return_direct", False))
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
    name: str = "beamlit_{function_config['name'].replace("-", "_")}"
    description: str = """{function_config['description']}"""
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
            response = requests.post("{BEAMLIT_RUN_URL}/{function_config['workspace']}/functions/{function_config['name']}", headers=headers, json={{{", ".join(f'"{param['name']}": {param['name']}' for param in function_config["parameters"])}}})
            return response.json(), {{}}
        except Exception as e:
            return repr(e), {{}}
'''

def generate_chain_code(beamlit_config: Dict, functions: List[Dict]) -> str:
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

def generate_functions(destination: str, beamlit_config: Dict, functions: List[Dict]):
    imports = '''from typing import Dict, List, Literal, Optional, Tuple, Type, Union
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.functions import BaseTool
from pydantic import BaseModel, Field
import requests
'''

    export_code = '\n\nfunctions = ['
    code = imports
    for function_config in functions:
        code += generate_function_code(beamlit_config, function_config)
        export_code += f'Beamlit{function_config["name"].title().replace("-", "")}(),'
    if beamlit_config.get('chain') and beamlit_config['chain'].get('enabled'):
        code += generate_chain_code(beamlit_config, functions)
    export_code = export_code[:-1]
    export_code += ']'
    with open(destination, "w") as f:
        f.write(code + export_code)

def run(destination: str):
    beamlit_config = parse_beamlit_yaml()
    functions = get_functions_from_beamlit(beamlit_config)
    generate_functions(destination, beamlit_config, functions)