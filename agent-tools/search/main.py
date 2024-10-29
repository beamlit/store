import os
from typing import Any

from langchain_community.tools.tavily_search.tool import (TavilyInput,
                                                          TavilySearchResults)


async def main(body: Any):
    api_key = os.getenv("TAVILY_API_KEY")
    input = TavilyInput(**body)
    tavily = TavilySearchResults(api_key=api_key, max_results=2)
    result = tavily.invoke(input.query)
    return result
