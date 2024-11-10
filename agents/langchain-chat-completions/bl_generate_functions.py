from typing import Dict, List

import requests
import yaml

from .parse_beamlit import parse_beamlit_yaml


def get_functions_from_beamlit(beamlit_config: Dict) -> List[Dict]:
    headers = {"X-Beamlit-Workspace": beamlit_config['workspace']}
    if beamlit_config.get('api_key'):
        headers["Api-Key"] = beamlit_config['api_key']
    elif beamlit_config.get('jwt'):
        headers["Authorization"] = f"Bearer {beamlit_config['jwt']}"

    response = requests.get(f"{beamlit_config['base_url']}/functions", headers=headers, params={"deployment": "true"})
    if response.status_code != 200:
        raise Exception(f"Failed to get functions from beamlit: {response.text}")
    functions = response.json()
    for name in beamlit_config['functions']:
        if not any(function['name'] == name for function in functions):
            raise Exception(f"Function {name} not found in beamlit")
    return functions

def generate_function_code(beamlit_config: Dict, function_config: Dict) -> str:
    name = function_config["name"].title().replace("-", "")
    deployment = [deployment for deployment in function_config["deployments"] if deployment["environment"] == beamlit_config["environment"]]
    if len(deployment) == 0:
        raise Exception(f"No deployment found for environment {beamlit_config['environment']}")
    deployment = deployment[0]
    args_list = ", ".join(f"{param['name']}: str" for param in deployment["parameters"])
    args_schema = "\n    ".join(
        f"{param['name']}: str = Field(description='{param.get('description', '')}')"
        for param in deployment["parameters"]
    )
    return_direct = str(deployment.get("return_direct", False))
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
            response = requests.post("{beamlit_config['run_url']}/{function_config['workspace']}/functions/{function_config['name']}", headers=headers, json={{{", ".join(f'"{param['name']}": {param['name']}' for param in deployment["parameters"])}}})
            return response.json(), {{}}
        except Exception as e:
            return repr(e), {{}}
'''

def generate_chain_code(beamlit_config: Dict, functions: List[Dict]) -> str:
    chain = beamlit_config['chain']
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

def generate_functions(destination: str, beamlit_config: Dict, functions: List[Dict]):
    imports = '''from typing import Dict, List, Literal, Optional, Tuple, Type, Union
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
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