import os
from typing import Any, Dict

from common.bl_config import BL_CONFIG
from fastapi import BackgroundTasks, Request
from langchain_community.tools.tavily_search.tool import TavilySearchResults
from pydantic import BaseModel, Field


async def main(request: Request, body: Dict[str, Any], background_tasks: BackgroundTasks):
    """
        displayName: Search
        description: A search engine optimized for comprehensive, accurate, and trusted results. Useful for when you need to answer questions about current events. Input should be a search query.
        configuration:
        - name: tavily_api_key
          displayName: Tavily API Key
          description: Tavily API key
          required: true
          secret: true
    """
    class SearchInput(BaseModel):
        query: str = Field(description="Query to search the web with.")

    apiKey = BL_CONFIG.get('tavily_api_key')
    if not apiKey:
        raise Exception("Tavily Key must be set to use this function")
    os.environ['TAVILY_API_KEY'] = apiKey
    input = SearchInput(**body)
    tavily = TavilySearchResults(apiKey=apiKey, max_results=2)
    result = tavily.invoke(input.query)
    return result
