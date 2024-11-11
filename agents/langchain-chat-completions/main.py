import json
import os
import uuid

from fastapi import Request
from langchain.agents import AgentExecutor, create_json_chat_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts.loading import load_prompt_from_config
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_openai import ChatOpenAI

from .beamlit import functions
from .bl_generate_functions import parse_beamlit_yaml
from .prompt import prompt

try:
    BL_CHAIN = json.loads(os.getenv("BL_CHAIN", None))
except:
    BL_CHAIN = None

def get_chat_model(config):
    if "provider" not in config:
        raise ValueError("Provider not found in configuration")
    if config['provider'] == 'openai':
        return ChatOpenAI(model=config["llm"], temperature=0, api_key=config["openai_api_key"])
    elif config['provider'] == 'anthropic':
        return ChatAnthropic(model=config["llm"], temperature=0, api_key=config["anthropic_api_key"])
    elif config['provider'] == 'mistral':
        return ChatMistralAI(model=config["llm"], temperature=0, api_key=config["mistral_api_key"])
    else:
        raise ValueError(f"Invalid provider: {config['provider']}")

# Create the agent
beamlit_config = parse_beamlit_yaml()
model = get_chat_model(beamlit_config)
agent = create_json_chat_agent(model, functions, prompt)
agent_executor = AgentExecutor(agent=agent, tools=functions)

async def chain_function(all_responses, agent_config):
    from .beamlit import BeamlitChain

    chain_functions = [BeamlitChain()]
    model = get_chat_model(beamlit_config)
    agent_two = create_json_chat_agent(model, chain_functions, prompt)
    agent_two_executor = AgentExecutor(agent=agent_two, tools=chain_functions)
    for chunk in agent_two_executor.stream({"input": json.dumps(all_responses)}, agent_config):
        if "output" in chunk:
            response = chunk["output"]
    return response

async def main(request: Request):
    sub = request.headers.get("X-Beamlit-Sub", str(uuid.uuid4()))
    agent_config = {"configurable": {"thread_id": sub}}
    response = ""
    body = await request.json()
    if body.get("inputs"):
        body["input"] = body["inputs"]

    all_responses = [body]
    for chunk in agent_executor.stream(body, agent_config):
        if "output" in chunk:
            response = chunk["output"]

    all_responses.append({"input": response})
    chain = beamlit_config['chain']
    if chain and chain.get('enabled'):
        response = await chain_function(all_responses, agent_config)
    return response

if __name__ == "__main__":
    main()
