import math
import operator
from typing import Any, Dict

from fastapi.requests import Request
from pydantic import BaseModel, Field


async def main(request: Request):
    """
    displayName: Math
    description: A function for performing mathematical calculations.
    """

    class MathInput(BaseModel):
        query: str = Field(description="The expression to evaluate.")

    body: Dict[str, Any] = await request.json()

    expr = MathInput(**body)
    safe_dict = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "pow": pow,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "pi": math.pi,
        "e": math.e,
    }

    # Add basic arithmetic operators
    safe_dict.update(
        {
            "+": operator.add,
            "-": operator.sub,
            "*": operator.mul,
            "/": operator.truediv,
            "**": operator.pow,
            "%": operator.mod,
        }
    )

    try:
        # Replace 'x' with '*'
        expr.query = expr.query.replace("x", "*")

        # Evaluate the expression in a restricted environment
        return eval(expr.query, {"__builtins__": {}}, safe_dict)
    except Exception as e:
        raise ValueError(f"Invalid expression: {str(e)}")
