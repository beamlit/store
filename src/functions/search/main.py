import os
from typing import Any, Dict

from beamlit.common.instrumentation import get_tracer
from langchain_community.tools.tavily_search.tool import TavilySearchResults
from pydantic import BaseModel, Field


async def main(
    body: Dict[str, Any],
    headers=None,
    query_params=None,
    **_
):
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
    with get_tracer().start_as_current_span("search") as span:
        span.set_attribute("query", body["query"])

        class SearchInput(BaseModel):
            query: str = Field(description="Search query.")

        api_key = os.getenv('TAVILY_API_KEY', os.getenv('BL_TAVILY_API_KEY'))
        if not api_key:
            raise Exception("Tavily Key must be set to use this function")

        os.environ['TAVILY_API_KEY'] = api_key
        input = SearchInput(**body)
        tavily = TavilySearchResults(api_key=api_key, max_results=2)
        result = tavily.invoke(input.query)
        return result
