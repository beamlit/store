from typing import Dict, List, Literal, Optional, Tuple, Type, Union

import requests
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class BeamlitMathZagInput(BaseModel):
    query: str = Field(description='The expression to evaluate.')

class BeamlitMathZag(BaseTool):
    name: str = "beamlit_math_zag"
    description: str = """A tool for performing mathematical calculations. if request to this tool fails it should return an error"""
    args_schema: Type[BaseModel] = BeamlitMathZagInput

    response_format: Literal["content_and_artifact"] = "content_and_artifact"
    return_direct: bool = False

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Tuple[Union[List[Dict[str, str]], str], Dict]:
        try:
            headers = {
                "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6ImJlYW1saXQiLCJ0eXAiOiJKV1QifQ.eyJhdWQiOlsiYmVhbWxpdCJdLCJlbWFpbCI6ImNoLnBsb3Vqb3V4QGdtYWlsLmNvbSIsImV4cCI6MTczODE3NDg2OSwiZmFtaWx5X25hbWUiOiJQbG91am91eCIsImdpdmVuX25hbWUiOiJDaHJpc3RvcGhlIiwiaWF0IjoxNzMwMzk4ODY5LCJpc3MiOiJodHRwczovL2FwaS5iZWFtbGl0LmRldi92MCIsImp0aSI6IkhGTENGTklTOVlBV1oxR1giLCJuYmYiOjE3MzAzOTg4NjksInNjb3BlIjoiKiIsInN1YiI6ImJjNjZiMTZmLTZiNWItNGY5Mi04NWMzLTkxNWFjNTc1NmIzMSIsInN1Yl90eXBlIjoidXNlciJ9.O3lY9v_HleObge3jH_vtGt1kSST1J15555ayDFfBpSMHHWzU8P_4lZOelCC8IB1NCvFYJ8sYhrXCxWSk54VEmjYn-W_0hPjW7MtS-jza0wYvWB3vtcxXUtyBOMcuoRzxZBXxBOKU0CuCDNZPEZ7I0XY3MvoVj0vTLpXNcT5vOMzj0Vch7yFlosBHGhikV5JkaUGc8Dz_7tmTSTzWGqoiLG9ccR0b1vuXLbAE6egK93Mr8lx3kAWawcP5JVEp_445rjO8R6XlsULVuWXJhc_F1VSSoZ2-xvje9C-0X7bktNaiVDrtdfS2x68Vgo-SDtVMKOKKbXN57-f9kiRGlgjkNbxjaQWZzWmcwKVLilLFIJXw6hzS0mkreRzdbtBYvuZWKbvCTwjtn_d1VsfjrK7APGDYzvSkFblkgQU0ixETobkH0_aA2pmAwpjItu-44OwbsBuv9QixH_-Cn5OIN3zwzYNH8VOGG5Y1E7rLP6Ugi0e-mJ1IZ-qG3oGa0YKjZ5ZNQb5hgkgkYYBXHt_xT6tN5u2SGuL8QdM9EBTyUJYW3wTkJLZv_TerehHSeuoeAdfmD1OJaPUykeygCWN4O0b-RsJhrNiEUITtMJPlJRVMmA9r59LVssF_omic64Jbm2xleaPsakY8Bjtw-VQeyrH3RL8jgUPectw9_RqevR6484Q"
            }
            response = requests.post("https://run.beamlit.net/development/tools/math-zag", headers=headers, json={"query": query})
            return response.json(), {}
        except Exception as e:
            return repr(e), {}

class BeamlitSearchZagInput(BaseModel):
    query: str = Field(description='Query to search the web with.')

class BeamlitSearchZag(BaseTool):
    name: str = "beamlit_search_zag"
    description: str = """A search engine optimized for comprehensive, accurate, and trusted results. Useful for when you need to answer questions about current events. Input should be a search query."""
    args_schema: Type[BaseModel] = BeamlitSearchZagInput

    response_format: Literal["content_and_artifact"] = "content_and_artifact"
    return_direct: bool = False

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Tuple[Union[List[Dict[str, str]], str], Dict]:
        return "The best burger in town is from In and Out", {}


class BeamlitBurgerOrder(BaseTool):
    name: str = "beamlit_burger_order"
    description: str = """A tool for ordering burgers and fries"""
    args_schema: Type[BaseModel] = BeamlitMathZagInput

    response_format: Literal["content_and_artifact"] = "content_and_artifact"
    return_direct: bool = False

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Tuple[Union[List[Dict[str, str]], str], Dict]:
        return f"From your query: {query}, I ordered a burger", {}

tools = [BeamlitMathZag(),BeamlitSearchZag()]