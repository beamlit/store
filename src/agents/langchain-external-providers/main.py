import logging
import time
import uuid

from fastapi import BackgroundTasks, Request, Response
from langchain_anthropic import ChatAnthropic
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from common.bl_config import BL_CONFIG
from common.bl_register_request import handle_chunk, register, send

# this is dynamically generated, so ignore linting
from .beamlit import chains, functions  # type: ignore

logger = logging.getLogger(__name__)

global model

model = None

def get_chat_model():
    if "provider" not in BL_CONFIG:
        raise ValueError("Provider not found in configuration")
    if BL_CONFIG['provider'] == 'openai':
        return ChatOpenAI(model=BL_CONFIG["model"], temperature=0, api_key=BL_CONFIG["openai_api_key"])
    elif BL_CONFIG['provider'] == 'anthropic':
        return ChatAnthropic(model=BL_CONFIG["model"], temperature=0, api_key=BL_CONFIG["anthropic_api_key"])
    elif BL_CONFIG['provider'] == 'mistral':
        return ChatMistralAI(model=BL_CONFIG["model"], temperature=0, api_key=BL_CONFIG["mistral_api_key"])
    else:
        raise ValueError(f"Invalid provider: {BL_CONFIG['provider']}")

async def ask_agent(request, body, tools, agent_config, background_tasks: BackgroundTasks):
    global model
    if model is None:
        model = get_chat_model()
        logger.info(f"Chat model configured, using: {BL_CONFIG['provider']}:{BL_CONFIG['model']}")

    memory = MemorySaver()
    agent = create_react_agent(model, tools, checkpointer=memory)
    all_responses = []
    start = time.time()
    for chunk in agent.stream({"messages": [("user", body["input"])]}, config=agent_config):
        end = time.time()
        background_tasks.add_task(handle_chunk, request, chunk, start, end)
        all_responses.append(chunk)
        start = end
    return all_responses

async def main(request: Request, background_tasks: BackgroundTasks):
    sub = request.headers.get("X-Beamlit-Sub", str(uuid.uuid4()))
    agent_config = {"configurable": {"thread_id": sub}}
    body = await request.json()
    if body.get("inputs"):
        body["input"] = body["inputs"]

    debug = request.query_params.get('debug') in ["true", "True", "TRUE"]
    background_tasks.add_task(register, request)
    responses = await ask_agent(request, body, chains + functions, agent_config, background_tasks)
    background_tasks.add_task(send, request, debug=debug)
    if debug:
        return responses
    else:
        content = responses[-1]["agent"]["messages"][-1].content
        return Response(content=content, headers={"Content-Type": "text/plain"}, status_code=200)


if __name__ == "__main__":
    main()
