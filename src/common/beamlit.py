from typing import Dict, List, Literal, Optional, Tuple, Type, Union

import requests
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from common.bl_config import BL_CONFIG


class BeamlitChainSearchAgentInput(BaseModel):
    input: str = Field(description='I do research on website for realtime information about the world')

class BeamlitChainSearchAgent(BaseTool):
    name: str = "beamlit_search_agent"
    description: str = """I do research on website for realtime information about the world"""
    args_schema: Type[BaseModel] = BeamlitChainSearchAgentInput

    response_format: Literal["content_and_artifact"] = "content_and_artifact"
    return_direct: bool = False

    def _run(
        self,
        input: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Tuple[Union[List[Dict[str, str]], str], Dict]:
        try:
            headers = {
                "X-Beamlit-Authorization": f"Bearer {BL_CONFIG['jwt']}"
            }
            response = requests.post("https://run.beamlit.dev/development/agents/search-agent", headers=headers, json={"input": input})
            if response.status_code >= 400:
                raise Exception(f"Failed to run tool search-agent, {response.status_code}::{response.text}")
            return response.json(), {}
        except Exception as e:
            return repr(e), {}


functions = []

chains = [BeamlitChainSearchAgent()]