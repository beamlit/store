import os
from typing import Any

from langchain_community.tools.tavily_search.tool import (TavilyInput,
                                                          TavilySearchResults)

from .parse_beamlit import parse_beamlit_yaml

# TODO: Move this to the sdk
config = parse_beamlit_yaml()

async def main(body: Any):
    api_key = config.get('tavily_api_key')
    if not api_key:
        raise Exception("Tavily Key must be set to use this function")
    input = TavilyInput(**body)
    tavily = TavilySearchResults(api_key=api_key, max_results=2)
    result = tavily.invoke(input.query)
    return result
