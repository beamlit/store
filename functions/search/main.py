import os
from typing import Any

from langchain_community.tools.tavily_search.tool import (TavilyInput,
                                                          TavilySearchResults)


async def main(body: Any, config):
    api_key = config.get('tavily_key')
    if not api_key:
        raise Exception("Tavily Key must be set to use this function")
    input = TavilyInput(**body)
    tavily = TavilySearchResults(api_key=api_key, max_results=2)
    result = tavily.invoke(input.query)
    return result
