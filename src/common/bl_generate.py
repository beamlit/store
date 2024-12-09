from typing import Dict, Tuple

from common.bl_config import BL_CONFIG


def getTitlesName(name: str) -> str:
    return name.title().replace("-", "").replace("_", "")


def generate_kit_function_code(function_config: Dict) -> Tuple[str, str]:
    export_code = ""
    code = ""
    for kit in function_config["kit"]:
        body = {
            "function": kit["name"],
            "workspace": function_config["workspace"],
            **kit,
        }
        new_code, export = generate_function_code(
            body, force_name_in_endpoint=function_config["function"], kit=True
        )
        code += new_code
        export_code += export
    return code, export_code


def generate_function_code(
    function_config: Dict, force_name_in_endpoint: str = "", kit: bool = False
) -> Tuple[str, str]:
    name = getTitlesName(function_config["function"])
    if len(function_config["parameters"]) > 0:
        args_list = ", ".join(
            f"{param['name']}: str" for param in function_config["parameters"]
        )
        args_list += ", "
    else:
        args_list = ""
    args_schema = ""
    for param in function_config["parameters"]:
        args_schema += f'{param["name"]}: str = Field(description="""{param.get("description", "")}""")\n    '
    if len(args_schema) == 0:
        args_schema = "pass"
    return_direct = str(function_config.get("return_direct", False))
    endpoint_name = force_name_in_endpoint or function_config["function"]
    body = f'{", ".join(f'"{param['name']}": {param['name']}' for param in function_config["parameters"])}'
    if kit is True:
        has_name = False
        for param in function_config["parameters"]:
            if param["name"] == "name":
                has_name = True
                break
        if not has_name:
            if len(body) > 0:
                body += ", "
            body += f'"name": "{function_config["function"]}"'
    return (
        f'''
class Beamlit{name}Input(BaseModel):
    {args_schema}

class Beamlit{name}(BaseTool):
    name: str = "beamlit_{function_config['function'].replace("-", "_")}"
    description: str = """{function_config['description']}"""
    args_schema: Type[BaseModel] = Beamlit{name}Input

    response_format: Literal["content_and_artifact"] = "content_and_artifact"
    return_direct: bool = {return_direct}

    def _run(self, {args_list} run_manager: Optional[CallbackManagerForToolRun] = None) -> Tuple[Union[List[Dict[str, str]], str], Dict]:
        try:
            headers = self.metadata.get("headers", {{}})
            params = self.metadata.get("params", {{}})
            response = requests.post("{BL_CONFIG['run_url']}/{BL_CONFIG['workspace']}/functions/{endpoint_name}", headers=headers, params=params, json={{{body}}})
            if response.status_code >= 400:
                logger.error(f"Failed to run function {name}, {{response.status_code}}::{{response.text}}")
                raise Exception(f"Failed to run function {name}, {{response.status_code}}::{{response.text}}")
            return response.json(), {{}}
        except Exception as e:
            return repr(e), {{}}
''',
        f'Beamlit{getTitlesName(function_config["function"])},',
    )


def generate_chain_code(agent: Dict) -> Tuple[str, str]:
    name = getTitlesName(agent["name"])
    return_direct = str(agent.get("return_direct", False))
    return (
        f'''
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
            headers = self.metadata.get("headers", {{}})
            params = self.metadata.get("params", {{}})
            response = requests.post("{BL_CONFIG['run_url']}/{BL_CONFIG['workspace']}/agents/{agent['name']}", headers=headers, params=params, json={{"input": input}})
            if response.status_code >= 400:
                logger.error(f"Failed to run tool {agent['name']}, {{response.status_code}}::{{response.text}}")
                raise Exception(f"Failed to run tool {agent['name']}, {{response.status_code}}::{{response.text}}")
            if response.headers.get("Content-Type") == "application/json":
                return response.json(), {{}}
            else:
                return response.text, {{}}
        except Exception as e:
            return repr(e), {{}}
''',
        f"BeamlitChain{name},",
    )


def generate(destination: str, dry_run: bool = False):
    imports = """from logging import getLogger
from typing import Dict, List, Literal, Optional, Tuple, Type, Union

import requests
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = getLogger(__name__)
"""

    export_code = "\n\nfunctions = ["
    export_chain = "\n\nchains = ["
    code = imports
    if BL_CONFIG.get("agent_functions") and len(BL_CONFIG["agent_functions"]) > 0:
        for function_config in BL_CONFIG["agent_functions"]:
            if function_config.get("kit") and len(function_config["kit"]) > 0:
                new_code, export = generate_kit_function_code(function_config)
                code += new_code
                export_code += export
            else:
                new_code, export = generate_function_code(function_config)
                code += new_code
                export_code += export
    if BL_CONFIG.get("agent_chain") and len(BL_CONFIG["agent_chain"]) > 0:
        for agent in BL_CONFIG["agent_chain"]:
            new_code, export = generate_chain_code(agent)
            code += new_code
            export_chain += export
    if BL_CONFIG.get("agent_functions") and len(BL_CONFIG["agent_functions"]) > 0:
        export_code = export_code[:-1]
    export_code += "]"
    if BL_CONFIG.get("agent_chain") and len(BL_CONFIG["agent_chain"]) > 0:
        export_chain = export_chain[:-1]
    export_chain += "]"
    content = code + export_code + export_chain
    if not dry_run:
        with open(destination, "w") as f:
            f.write(content)
    return content
