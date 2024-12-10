import math
import operator
from typing import Any, Dict

from fastapi import BackgroundTasks, Request
from pydantic import BaseModel, Field

from common.bl_instrumentation import get_tracer


async def main(
    request: Request,
    body: Dict[str, Any],
    background_tasks: BackgroundTasks,
):
    """
    display_name: Math
    description: A function for performing mathematical calculations.
    """
    with get_tracer().start_as_current_span("search") as span:
        span.set_attribute("query", body["query"])

        class MathInput(BaseModel):
            query: str = Field(description="The expression to evaluate.")

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
