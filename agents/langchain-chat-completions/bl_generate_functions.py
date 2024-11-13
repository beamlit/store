from typing import Dict, List

import requests
import yaml

from .bl_config import BL_CONFIG


def get_functions_from_beamlit() -> List[Dict]:
    headers = {"X-Beamlit-Workspace": BL_CONFIG['workspace']}

    if BL_CONFIG.get('api_key'):
        headers["Api-Key"] = BL_CONFIG['api_key']
    elif BL_CONFIG.get('jwt'):
        headers["X-Beamlit-Authorization"] = f"Bearer {BL_CONFIG['jwt']}"

    response = requests.get(f"{BL_CONFIG['base_url']}/functions", headers=headers, params={"deployment": "true"})
    if response.status_code != 200:
        raise Exception(f"Failed to get functions from beamlit: {response.text}")
    functions = response.json()
    return_functions = []
    for function in functions:
        if function['name'] in BL_CONFIG['functions']:
            return_functions.append(function)
    for f in BL_CONFIG['functions']:
        if not any(function['name'] == f for function in return_functions):
            raise Exception(f"Function {f} not found in beamlit")
    return return_functions

def get_agents_from_beamlit() -> List[Dict]:
    headers = {"X-Beamlit-Workspace": BL_CONFIG['workspace']}

    if BL_CONFIG.get('api_key'):
        headers["Api-Key"] = BL_CONFIG['api_key']
    elif BL_CONFIG.get('jwt'):
        headers["X-Beamlit-Authorization"] = f"Bearer {BL_CONFIG['jwt']}"

    response = requests.get(f"{BL_CONFIG['base_url']}/agents", headers=headers, params={"deployment": "true"})
    if response.status_code != 200:
        raise Exception(f"Failed to get agents from beamlit: {response.text}")
    agents = response.json()
    return_agents = []
    for a in BL_CONFIG['agent_chain']:
        if not a.get("enabled", True):
            continue
        find_agent = None
        for agent in agents:
            if agent['name'] == a["name"]:
                find_agent = agent
                break
        if not find_agent:
            raise Exception(f"Agent {a['name']} not found in beamlit")
        if a.get("description"):
            find_agent["description"] = a["description"]
        return_agents.append(find_agent)
    return return_agents

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
                "X-Beamlit-Authorization": f"Bearer {{BL_CONFIG['jwt']}}"
            }}'''
    else:
        headers = f'''{{
                "X-Beamlit-Api-Key": BL_CONFIG['api_key']
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
            if response.status_code >= 400:
                raise Exception(f"Failed to run tool {name}, {{response.status_code}}::{{response.text}}")
            return response.json(), {{}}
        except Exception as e:
            return repr(e), {{}}
'''

def generate_chain_code(agent: Dict) -> str:
    name = agent["name"].title().replace("-", "")
    deployment = [deployment for deployment in agent["deployments"] if deployment["environment"] == BL_CONFIG["environment"]]
    if len(deployment) == 0:
        raise Exception(f"No deployment found for environment {BL_CONFIG['environment']}")
    deployment = deployment[0]
    return_direct = str(deployment.get("return_direct", False))
    if BL_CONFIG.get('jwt'):
        headers = f'''{{
                "X-Beamlit-Authorization": f"Bearer {{BL_CONFIG['jwt']}}"
            }}'''
    else:
        headers = f'''{{
                "X-Beamlit-Api-Key": BL_CONFIG['api_key']
            }}'''
    return f'''
class BeamlitChain{name}Input(BaseModel):
    input: str = Field(description='{deployment['description']}')

class BeamlitChain{name}(BaseTool):
    name: str = "beamlit_{agent['name'].replace("-", "_")}"
    description: str = """{deployment['description']}"""
    args_schema: Type[BaseModel] = BeamlitChain{name}Input

    response_format: Literal["content_and_artifact"] = "content_and_artifact"
    return_direct: bool = {return_direct}

    def _run(
        self,
        input: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Tuple[Union[List[Dict[str, str]], str], Dict]:
        try:
            headers = {headers}
            response = requests.post("{BL_CONFIG['run_url']}/{agent['workspace']}/agents/{agent['name']}", headers=headers, json={{"input": input}})
            if response.status_code >= 400:
                raise Exception(f"Failed to run tool {agent['name']}, {{response.status_code}}::{{response.text}}")
            return response.json(), {{}}
        except Exception as e:
            return repr(e), {{}}
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
    export_chain = '\n\nchains = ['
    code = imports
    for function_config in functions:
        code += generate_function_code(function_config)
        export_code += f'Beamlit{function_config["name"].title().replace("-", "")}(),'
    if BL_CONFIG.get('agent_chain') and len(BL_CONFIG['agent_chain']) > 0:
        agents = get_agents_from_beamlit()
        for agent in agents:
            code += generate_chain_code(agent)
            export_chain += f'BeamlitChain{agent["name"].title().replace("-", "")}(),'
    export_code = export_code[:-1]
    export_code += ']'
    export_chain = export_chain[:-1]
    export_chain += ']'
    with open(destination, "w") as f:
        f.write(code + export_code + export_chain)

def run(destination: str):
    functions = get_functions_from_beamlit()
    generate_functions(destination, functions)