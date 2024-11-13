import json
import logging
import uuid

from fastapi import Request
from langchain.agents import AgentExecutor, create_json_chat_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts.loading import load_prompt_from_config
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_openai import ChatOpenAI

from .beamlit import functions
from .bl_config import BL_CONFIG
from .prompt import prompt

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


async def chain_function(all_responses, agent_config):
    from .beamlit import chains

    global chain_model

    if chain_model is None:
        chain_model = get_chat_model()
        logger.info(f"Chain model configured, using: {BL_CONFIG['provider']}:{BL_CONFIG['llm']}")
    agent_two = create_json_chat_agent(chain_model, chains, prompt)
    agent_two_executor = AgentExecutor(agent=agent_two, tools=chains)
    for chunk in agent_two_executor.stream({"input": json.dumps(all_responses)}, agent_config):
        logger.debug(chunk)
        if "output" in chunk:
            response = chunk["output"]
    return response

async def main(request: Request):
    global model

    sub = request.headers.get("X-Beamlit-Sub", str(uuid.uuid4()))
    agent_config = {"configurable": {"thread_id": sub}}
    response = ""
    body = await request.json()
    if body.get("inputs"):
        body["input"] = body["inputs"]

    # Create the agent
    if model is None:
        model = get_chat_model()
        logger.info(f"Chat model configured, using: {BL_CONFIG['provider']}:{BL_CONFIG['llm']}")

    agent = create_json_chat_agent(model, functions, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=functions)

    all_responses = [body]
    for chunk in agent_executor.stream(body, agent_config):
        logger.debug(chunk)
        if "output" in chunk:
            response = chunk["output"]

    all_responses.append({"input": response})
    chain = BL_CONFIG.get('agent_chain')
    if chain and len(chain) > 0:
        response = await chain_function(all_responses, agent_config)
    return response

if __name__ == "__main__":
    main()
