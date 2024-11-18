import logging
import uuid

from fastapi import Request, Response
from langchain_anthropic import ChatAnthropic
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from common.bl_config import BL_CONFIG

# this is dynamically generated, so ignore linting
from .beamlit import chains, functions  # type: ignore

logger = logging.getLogger(__name__)

global model
global chain_model

model = None
chain_model = None

def get_chat_model():
    if "provider" not in BL_CONFIG:
        raise ValueError("Provider not found in configuration")
    if BL_CONFIG['provider'] == 'openai':
        return ChatOpenAI(model=BL_CONFIG["llm"], temperature=0, api_key=BL_CONFIG["openai_api_key"])
    elif BL_CONFIG['provider'] == 'anthropic':
        return ChatAnthropic(model=BL_CONFIG["llm"], temperature=0, api_key=BL_CONFIG["anthropic_api_key"])
    elif BL_CONFIG['provider'] == 'mistral':
        return ChatMistralAI(model=BL_CONFIG["llm"], temperature=0, api_key=BL_CONFIG["mistral_api_key"])
    else:
        raise ValueError(f"Invalid provider: {BL_CONFIG['provider']}")

async def ask_agent(body, tools, agent_config):
    global model
    if model is None:
        model = get_chat_model()
        logger.info(f"Chat model configured, using: {BL_CONFIG['provider']}:{BL_CONFIG['llm']}")

    memory = MemorySaver()
    agent = create_react_agent(model, tools, checkpointer=memory)
    all_responses = []
    for chunk in agent.stream({"messages": [("user", body["input"])]}, config=agent_config):
        # Do update asynchronously of task in control plane, use a queue to update the task
        all_responses.append(chunk)
    return all_responses

async def main(request: Request):
    sub = request.headers.get("X-Beamlit-Sub", str(uuid.uuid4()))
    agent_config = {"configurable": {"thread_id": sub}}
    body = await request.json()
    if body.get("inputs"):
        body["input"] = body["inputs"]

    responses = await ask_agent(body, chains + functions, agent_config)
    all_responses = request.query_params.get('all_responses') in ["true", "True", "TRUE"]
    if all_responses:
        return responses
    else:
        content = responses[-1]["agent"]["messages"][-1].content
        return Response(content=content, headers={"Content-Type": "text/plain"}, status_code=200)


if __name__ == "__main__":
    main()
