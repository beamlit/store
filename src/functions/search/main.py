import os
from typing import Any

from langchain_community.tools.tavily_search.tool import (TavilyInput,
                                                          TavilySearchResults)

from common.bl_config import BL_CONFIG


async def main(body: Any):
    api_key = BL_CONFIG.get('tavily_api_key')
    if not api_key:
        raise Exception("Tavily Key must be set to use this function")
    os.environ['TAVILY_API_KEY'] = api_key
    input = TavilyInput(**body)
    tavily = TavilySearchResults(api_key=api_key, max_results=2)
    result = tavily.invoke(input.query)
    return result
