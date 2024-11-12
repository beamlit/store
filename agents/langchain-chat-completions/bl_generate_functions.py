from typing import Dict, List

import requests
import yaml

from .bl_config import BL_CONFIG


def get_functions_from_beamlit() -> List[Dict]:
    headers = {"X-Beamlit-Workspace": BL_CONFIG['workspace']}
    if BL_CONFIG.get('api_key'):
        headers["Api-Key"] = BL_CONFIG['api_key']
    elif BL_CONFIG.get('jwt'):
        headers["Authorization"] = f"Bearer {BL_CONFIG['jwt']}"

    response = requests.get(f"{BL_CONFIG['base_url']}/functions", headers=headers, params={"deployment": "true"})
    if response.status_code != 200:
        raise Exception(f"Failed to get functions from beamlit: {response.text}")
    functions = response.json()
    for name in BL_CONFIG['functions']:
        if not any(function['name'] == name for function in functions):
            raise Exception(f"Function {name} not found in beamlit")
    return functions

def generate_function_code(function_config: Dict) -> str:
    name = function_config["name"].title().replace("-", "")
    deployment = [deployment for deployment in function_config["deployments"] if deployment["environment"] == BL_CONFIG["environment"]]
    if len(deployment) == 0:
        raise Exception(f"No deployment found for environment {BL_CONFIG['environment']}")
    deployment = deployment[0]
    args_list = ", ".join(f"{param['name']}: str" for param in deployment["parameters"])
    args_schema = "\n    ".join(
        f"{param['name']}: str = Field(description='{param.get('description', '')}')"
        for param in deployment["parameters"]
    )
    return_direct = str(deployment.get("return_direct", False))
    if BL_CONFIG.get('jwt'):
        headers = f'''{{
                "Authorization": f"Bearer {{BL_CONFIG['jwt']}}"
            }}'''
    else:
        headers = f'''{{
                "Api-Key": BL_CONFIG['api_key']
            }}'''
    return f'''
class Beamlit{name}Input(BaseModel):
    {args_schema}

class Beamlit{name}(BaseTool):
    name: str = "beamlit_{function_config['name'].replace("-", "_")}"
    description: str = """{deployment['description']}"""
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
            response = requests.post("{BL_CONFIG['run_url']}/{function_config['workspace']}/functions/{function_config['name']}", headers=headers, json={{{", ".join(f'"{param['name']}": {param['name']}' for param in deployment["parameters"])}}})
            return response.json(), {{}}
        except Exception as e:
            return repr(e), {{}}
'''

def generate_chain_code(functions: List[Dict]) -> str:
    chain = BL_CONFIG['chain']
    return f'''
class BeamlitChainInput(BaseModel):
    query: str = Field(description='{chain['description']}')


class BeamlitChain(BaseTool):
    name: str = "{chain['name']}"
    description: str = """{chain['description']}"""
    args_schema: Type[BaseModel] = BeamlitChainInput

    response_format: Literal["content_and_artifact"] = "content_and_artifact"
    return_direct: bool = False

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Tuple[Union[List[Dict[str, str]], str], Dict]:
        return f"From your query: {{query}}, I ordered a burger", {{}}
'''

def generate_functions(destination: str, functions: List[Dict]):
    imports = '''from typing import Dict, List, Literal, Optional, Tuple, Type, Union
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import requests
from .bl_config import BL_CONFIG
'''

    export_code = '\n\nfunctions = ['
    code = imports
    for function_config in functions:
        code += generate_function_code(function_config)
        export_code += f'Beamlit{function_config["name"].title().replace("-", "")}(),'
    if BL_CONFIG.get('chain') and BL_CONFIG['chain'].get('enabled'):
        code += generate_chain_code(functions)
    export_code = export_code[:-1]
    export_code += ']'
    with open(destination, "w") as f:
        f.write(code + export_code)

def run(destination: str):
    functions = get_functions_from_beamlit()
    generate_functions(destination, functions)