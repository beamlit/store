from typing import Dict, Tuple

from common.bl_config import BL_CONFIG


def getTitlesName(name: str) -> str:
    return name.title().replace("-", "").replace("_", "")

def generate_kit_function_code(function_config: Dict) -> Tuple[str, str]:
    export_code = ""
    code = ""
    for kit in function_config["kit"]:
        body = {"function": kit["name"], "workspace": function_config["workspace"], **kit}
        new_code, export = generate_function_code(body, force_name_in_endpoint=function_config["function"])
        code += new_code
        export_code += export
    return code, export_code

def generate_function_code(function_config: Dict, force_name_in_endpoint: str = "") -> Tuple[str, str]:
    name = getTitlesName(function_config["function"])
    args_list = ", ".join(f"{param['name']}: str" for param in function_config["parameters"])
    args_schema = ""
    for param in function_config["parameters"]:
        args_schema += f'{param["name"]}: str = Field(description="""{param.get("description", "")}""")\n    '

    return_direct = str(function_config.get("return_direct", False))
    if BL_CONFIG.get('jwt'):
        headers = f'''{{
                "X-Beamlit-Authorization": f"Bearer {{BL_CONFIG['jwt']}}"
            }}'''
    else:
        headers = f'''{{
                "X-Beamlit-Api-Key": BL_CONFIG['api_key']
            }}'''
    endpoint_name = force_name_in_endpoint or function_config["function"]
    return f'''
class Beamlit{name}Input(BaseModel):
    {args_schema}

class Beamlit{name}(BaseTool):
    name: str = "beamlit_{function_config['function'].replace("-", "_")}"
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
            response = requests.post("{BL_CONFIG['run_url']}/{function_config['workspace']}/functions/{endpoint_name}", headers=headers, json={{{", ".join(f'"{param['name']}": {param['name']}' for param in function_config["parameters"])}}})
            if response.status_code >= 400:
                raise Exception(f"Failed to run tool {name}, {{response.status_code}}::{{response.text}}")
            return response.json(), {{}}
        except Exception as e:
            return repr(e), {{}}
''', f'Beamlit{getTitlesName(function_config["function"])}(),'

def generate_chain_code(agent: Dict) -> Tuple[str, str]:
    name = getTitlesName(agent["name"])
    return_direct = str(agent.get("return_direct", False))
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
    input: str = Field(description='{agent['description']}')

class BeamlitChain{name}(BaseTool):
    name: str = "beamlit_chain_{agent['name'].replace("-", "_")}"
    description: str = """{agent['description']}"""
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
            response = requests.post("{BL_CONFIG['run_url']}/{BL_CONFIG['workspace']}/agents/{agent['name']}", headers=headers, json={{"input": input}})
            if response.status_code >= 400:
                raise Exception(f"Failed to run tool {agent['name']}, {{response.status_code}}::{{response.text}}")
            if response.headers.get("Content-Type") == "application/json":
                return response.json(), {{}}
            else:
                return response.text, {{}}
        except Exception as e:
            return repr(e), {{}}
''', f'BeamlitChain{name}(),'

def run(destination: str):
    imports = '''from typing import Dict, List, Literal, Optional, Tuple, Type, Union
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import requests
from common.bl_config import BL_CONFIG
'''

    export_code = '\n\nfunctions = ['
    export_chain = '\n\nchains = ['
    code = imports
    if BL_CONFIG.get('agent_functions') and len(BL_CONFIG['agent_functions']) > 0:
        for function_config in BL_CONFIG['agent_functions']:
            if function_config.get("kit") and len(function_config["kit"]) > 0:
                new_code, export = generate_kit_function_code(function_config)
                code += new_code
                export_code += export
            else:
                new_code, export = generate_function_code(function_config)
                code += new_code
                export_code += export
    if BL_CONFIG.get('agent_chain') and len(BL_CONFIG['agent_chain']) > 0:
        for agent in BL_CONFIG['agent_chain']:
            print(agent)
            new_code, export = generate_chain_code(agent)
            code += new_code
            export_chain += export
    if BL_CONFIG.get('agent_functions') and len(BL_CONFIG['agent_functions']) > 0:
        export_code = export_code[:-1]
    export_code += ']'
    if BL_CONFIG.get('agent_chain') and len(BL_CONFIG['agent_chain']) > 0:
        export_chain = export_chain[:-1]
    export_chain += ']'
    with open(destination, "w") as f:
        f.write(code + export_code + export_chain)