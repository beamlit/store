import sys

sys.path.insert(0, "src")

import ast
import base64
import importlib
import inspect
import os
from pathlib import Path

import requests
import yaml

mapping = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
}


def get_parameters(func):
    parameters = []
    source = inspect.getsource(func)
    tree = ast.parse(source)
    # Find class definitions inside the function
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Instantiate the class to get its fields
            for class_node in node.body:
                if isinstance(class_node, ast.AnnAssign):
                    # Get field description from model_fields if it exists

                    if hasattr(class_node, "value"):
                        field_name = class_node.target.id
                        field_type = mapping.get(class_node.annotation.id, "string")
                        field_description = [
                            kw.value.value
                            for kw in class_node.value.keywords
                            if kw.arg == "description"
                        ]
                        field_required = (
                            len(
                                [
                                    kw.value.value
                                    for kw in class_node.value.keywords
                                    if kw.arg == "default"
                                ]
                            )
                            > 0
                        )
                        field_description = (
                            len(field_description) > 0 and field_description[0] or ""
                        )
                        parameters.append(
                            {
                                "name": field_name,
                                "type": field_type,
                                "description": field_description,
                                "required": field_required,
                            }
                        )
            # Get fields from parent classes
            for base in node.bases:
                if isinstance(base, ast.Name):
                    try:
                        # Try to get the parent class from the module
                        parent_class = getattr(sys.modules[func.__module__], base.id)
                        # Get fields from parent class if it's a Pydantic model
                        if hasattr(parent_class, "model_fields"):
                            for key, value in parent_class.model_fields.items():
                                print(value.annotation.__name__)
                                parameters.append(
                                    {
                                        "name": key,
                                        "type": mapping.get(
                                            value.annotation.__name__, "string"
                                        ),
                                        "description": value.description,
                                        "required": not hasattr(value, "default"),
                                    }
                                )
                    except (AttributeError, KeyError):
                        pass
    return parameters


def handle_kit(kit_path):
    # Change to src directory to allow proper imports
    kit = importlib.import_module(str(kit_path).replace("/", ".").replace("src.", ""))

    kit_definitions = []
    for func_name in dir(kit):
        if func_name.startswith("_") or not callable(getattr(kit, func_name)):
            continue

        func = getattr(kit, func_name)
        # Replace \n and any number of consecutive spaces with a single space
        description = func.__doc__.strip().replace("\n", " ")
        description = " ".join(description.split())
        parameters = get_parameters(func)
        kit_definitions.append(
            {
                "name": func_name,
                "description": description,
                "parameters": parameters,
            }
        )
    return kit_definitions


def push_store(type, package):
    store_url = os.environ.get("STORE_URL", "https://api.beamlit.dev/v0")
    admin_username = os.environ.get("ADMIN_USERNAME")
    admin_password = os.environ.get("ADMIN_PASSWORD")

    auth = base64.b64encode(f"{admin_username}:{admin_password}".encode()).decode()

    response = requests.put(
        f"{store_url}/admin/store/{type}/{package['name']}",
        json=package,
        headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"},
        timeout=30,
    )
    if response.status_code != 200:
        error_text = response.text
        raise Exception(
            f"Failed to push {package['name']} to store, cause {error_text}"
        )


def run():
    type = os.environ["PACKAGE_TYPE"]
    resource = os.environ["PACKAGE_NAME"]
    print(f"Handling {type} {resource}")

    base_path = Path(f"src/{type}/{resource}")
    kit_path = base_path / "kit"
    kit = None
    if kit_path.exists():
        kit = handle_kit(kit_path)

    mod = importlib.import_module(
        str(base_path).replace("/", ".").replace("src.", "") + ".main"
    )
    func = getattr(mod, "main")
    value = {
        "name": resource,
        "image": os.environ.get("IMAGE"),
        "description": "",
        "parameters": [],
    }
    if kit:
        value["kit"] = kit
    try:
        tmp_value = yaml.safe_load(func.__doc__ or "")
        if isinstance(tmp_value, dict):
            for key, val in tmp_value.items():
                value[key] = val
        else:
            value["description"] = tmp_value
            value["configuration"] = {}
        parameters = get_parameters(func)
        value["parameters"] = parameters
    except Exception as e:
        print(f"Could not parse value from docstring, {e}")

    print(f"Pushing {type} {resource} to store")
    push_store(type, value)
    print(f"Pushed {type} {resource} to store")


if __name__ == "__main__":
    run()
