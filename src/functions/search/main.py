import os
from typing import Any, Dict

from fastapi import BackgroundTasks, Request
from langchain_community.tools.tavily_search.tool import TavilySearchResults
from pydantic import BaseModel, Field

from common.bl_config import BL_CONFIG
from common.bl_instrumentation import get_tracer


async def main(
    request: Request,
    body: Dict[str, Any],
    background_tasks: BackgroundTasks,
):
    """
    display_name: Search
    description: A search engine optimized for comprehensive, accurate, and trusted results. Useful for when you need to answer questions about current events. Input should be a search query.
    configuration:
    - name: tavily_api_key
      display_name: Tavily API Key
      description: Tavily API key
      required: true
      secret: true
    """
    with get_tracer().start_as_current_span("search") as span:
        span.set_attribute("query", body["query"])

        class SearchInput(BaseModel):
            query: str = Field(description="Query to search the web with.")

        api_key = BL_CONFIG.get("tavily_api_key")
        if not api_key:
            raise Exception("Tavily Key must be set to use this function")
        os.environ["TAVILY_API_KEY"] = api_key
        input = SearchInput(**body)
        tavily = TavilySearchResults(api_key=api_key, max_results=2)
        result = tavily.invoke(input.query)
        return result
