from datetime import datetime, timezone
from logging import getLogger

import requests
from fastapi import Request

from common.bl_config import BL_CONFIG

history = {}

logger = getLogger(__name__)

def set_event(request, id, event):
    global history

    request_id = request.headers["x-request-id"]
    rhistory = history[request_id]
    rhistory["tmp_events"][id] = event

def get_event(request, id):
    global history

    request_id = request.headers["x-request-id"]
    rhistory = history[request_id]
    return rhistory["tmp_events"].get(id) or {}

def find_function_name(function_name: str) -> str:
    for function_config in BL_CONFIG['agent_functions']:
        if function_config['function'] == function_name:
            return function_config['function']
    for function_config in BL_CONFIG['agent_functions']:
        if function_config.get("kit") and len(function_config["kit"]) > 0:
            for kit in function_config["kit"]:
                if kit["name"] == function_name:
                    return function_config['function']
    return function_name

def handle_chunk_tools(request, chunk, start_dt, end_dt):
    messages = chunk["tools"]["messages"]
    for message in messages:
        # that means this is a request to send calls
        if message.content != "":
            event = get_event(request, message.tool_call_id)
            event["end"] = end_dt
            event_status = "failed" if message.content.startswith("Exception") else "success"
            if event_status == "failed":
                event["error"] = message.content
            event["status"] = event_status
            set_event(request, message.tool_call_id, event)

def handle_chunk_agent(request, chunk, start_dt, end_dt):
    messages = chunk["agent"]["messages"]
    for message in messages:
        # that means this is a request to send calls
        if message.content == "" and message.tool_calls:
            for tool in message.tool_calls:
                event = get_event(request, tool["id"])
                event["id"] = tool["id"]
                event_type = "agent" if "beamlit_chain_" in tool["name"] else "function"
                event["start"] = start_dt
                if event_type == "agent":
                    event["name"] = tool["name"].replace("beamlit_chain_", "", 1)
                else:
                    tool_name = tool["name"].replace("beamlit_", "", 1)
                    event["name"] = find_function_name(tool_name)
                    if event["name"] != tool_name:
                        event["sub_function"] = tool_name
                event["type"] = event_type
                event["parameters"] = tool.get("args")
                event["status"] = "running"
                set_event(request, tool["id"], event)

async def handle_chunk(request, chunk, start: float, end: float, debug=False):
    global history

    # Get local timezone offset from UTC
    local_dt = datetime.now()
    tz = timezone(local_dt.astimezone().utcoffset())
    start_dt = datetime.fromtimestamp(start, tz=tz).isoformat()
    end_dt = datetime.fromtimestamp(end, tz=tz).isoformat()
    if "agent" in chunk:
        handle_chunk_agent(request, chunk, start_dt, end_dt)
    elif "tools" in chunk:
        handle_chunk_tools(request, chunk, start_dt, end_dt)

def send_to_beamlit(request_id, rhistory):
    name = BL_CONFIG['name']
    env = BL_CONFIG['environment']
    headers = {"X-Beamlit-Workspace": BL_CONFIG['workspace'], "X-Beamlit-Environment": env}

    if BL_CONFIG.get('api_key'):
        headers["Api-Key"] = BL_CONFIG['api_key']
    elif BL_CONFIG.get('jwt'):
        headers["X-Beamlit-Authorization"] = f"Bearer {BL_CONFIG['jwt']}"
    url = f"{BL_CONFIG['base_url']}/agents/{name}/deployments/{env}/history/{request_id}"

    response = requests.put(url, headers=headers, json=rhistory)
    if response.status_code != 200:
        logger.error(f"Failed to send history to beamlit: {response.text}")

async def send(request: Request, debug=False):
    request_id = request.headers["x-request-id"]
    rhistory = history[request_id]
    for _, event in rhistory["tmp_events"].items():
        rhistory["events"].append(event)
    rhistory["events"].sort(key=lambda x: x["start"])
    if debug is True:
        send_to_beamlit(request_id, rhistory)


async def register(request: Request, debug=False):
    global history

    request_id = request.headers["x-request-id"]
    history[request_id] = {
        "status": "running",
        "environment": BL_CONFIG["environment"],
        "agent": BL_CONFIG["name"],
        "workspace": BL_CONFIG["workspace"],
        "events": [],
        "tmp_events": {}
    }