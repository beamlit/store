import json
import time
from datetime import datetime, timezone
from logging import getLogger

import requests
from asgi_correlation_id import correlation_id

from common.bl_config import BL_CONFIG

history = {}

logger = getLogger(__name__)

def get_date_from_time(time: float):
    local_dt = datetime.now()
    tz = timezone(local_dt.astimezone().utcoffset())
    return datetime.fromtimestamp(time, tz=tz).isoformat()

def set_event(id, event):
    global history

    request_id = correlation_id.get() or ""
    rhistory = history[request_id]
    rhistory["tmp_events"][id] = event

def get_event(id):
    global history

    request_id = correlation_id.get() or ""
    rhistory = history[request_id]
    return rhistory["tmp_events"].get(id) or {}

def find_function_name(function_name: str) -> str:
    for function_config in BL_CONFIG['agent_functions']:
        if function_config['function'] == function_name:
            return function_config['function'].replace("_", "")
    for function_config in BL_CONFIG['agent_functions']:
        if function_config.get("kit") and len(function_config["kit"]) > 0:
            for kit in function_config["kit"]:
                if kit["name"] == function_name:
                    return function_config['function'].replace("_", "")
    return function_name

def handle_chunk_tools(chunk, start_dt, end_dt):
    messages = chunk["tools"]["messages"]
    for message in messages:
        # that means this is a request to send calls
        if message.content != "":
            event = get_event(message.tool_call_id)
            event["end"] = end_dt
            event_status = "failed" if message.status == "error" else "success"
            if event_status == "failed":
                event["error"] = message.content
            event["status"] = event_status
            set_event(message.tool_call_id, event)

def handle_chunk_agent(chunk, start_dt, end_dt):
    messages = chunk["agent"]["messages"]
    for message in messages:
        # that means this is a request to send calls
        if message.content == "" and message.tool_calls:
            for tool in message.tool_calls:
                event = get_event(tool["id"])
                event["id"] = tool["id"]
                event_type = "agent" if "beamlit_chain_" in tool["name"] else "function"
                event["start"] = start_dt
                if event_type == "agent":
                    event["name"] = tool["name"].replace("beamlit_chain_", "", 1).replace("_", "-")
                else:
                    tool_name = tool["name"].replace("beamlit_", "", 1)
                    event["name"] = find_function_name(tool_name)
                    if event["name"] != tool_name:
                        event["sub_function"] = tool_name
                event["type"] = event_type
                event["parameters"] = tool.get("args")
                event["status"] = "running"
                set_event(tool["id"], event)

async def handle_chunk(chunk, start: float, end: float, debug=False):
    global history

    start_dt = get_date_from_time(start)
    end_dt = get_date_from_time(end)
    if "agent" in chunk:
        handle_chunk_agent(chunk, start_dt, end_dt)
    elif "tools" in chunk:
        handle_chunk_tools(chunk, start_dt, end_dt)

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

async def send(debug=False):
    request_id = correlation_id.get() or ""
    rhistory = history[request_id]
    for _, event in rhistory["tmp_events"].items():
        rhistory["events"].append(event)
    rhistory["events"].sort(key=lambda x: x["start"])
    rhistory["end"] = get_date_from_time(time.time())
    status = "success" if all(event["status"] == "success" for event in rhistory["events"]) else "failed"
    if len(rhistory["events"]) > 0:
        status = rhistory["events"][-1]["status"]
    else:
        status = "success"
    rhistory["status"] = status
    if debug is True:
        send_to_beamlit(request_id, rhistory)
    else:
        logger.info(f"Skipping sending history to beamlit for request: {request_id}")

async def register(start: float, debug=False):
    global history

    request_id = correlation_id.get() or ""
    history[request_id] = {
        "status": "running",
        "environment": BL_CONFIG["environment"],
        "agent": BL_CONFIG["name"],
        "workspace": BL_CONFIG["workspace"],
        "start": get_date_from_time(start),
        "events": [],
        "tmp_events": {}
    }