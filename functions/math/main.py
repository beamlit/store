import math
import operator
from typing import Any

from pydantic import BaseModel

from .parse_beamlit import parse_beamlit_yaml

# TODO: Move this to the sdk
config = parse_beamlit_yaml()

class Expression(BaseModel):
    query: str

def evaluate_math(expr: Expression) -> float:
    """
    Safely evaluates a mathematical expression string.
    Supports basic arithmetic operations and common math functions.
    """
    # Define allowed mathematical operations
    safe_dict = {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'pow': pow,
        'sqrt': math.sqrt,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'pi': math.pi,
        'e': math.e
    }

    # Add basic arithmetic operators
    safe_dict.update({
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.truediv,
        '**': operator.pow,
        '%': operator.mod
    })

    try:
        # Replace 'x' with '*'
        expr.query = expr.query.replace('x', '*')

        # Evaluate the expression in a restricted environment
        return eval(expr.query, {"__builtins__": {}}, safe_dict)
    except Exception as e:
        raise ValueError(f"Invalid expression: {str(e)}")

async def main(body: Any):
    expr = Expression(**body)
    return evaluate_math(expr)
