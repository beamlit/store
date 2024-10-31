import uuid
from typing import Any

from fastapi import Request
from langchain import hub
from langchain.agents import AgentExecutor, create_json_chat_agent
from langchain_core.prompts.loading import load_prompt_from_config
from langchain_openai import ChatOpenAI

from .beamlit import tools
from .prompt import prompt

chain = True
# Create the agent

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
agent = create_json_chat_agent(model, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)

async def chain_function(all_responses, config):
    from .beamlit import BeamlitChain

    chain_tools = [BeamlitChain()]
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent_two = create_json_chat_agent(llm, chain_tools, prompt)
    agent_two_executor = AgentExecutor(agent=agent_two, tools=chain_tools)
    for chunk in agent_two_executor.stream({"input": all_responses}, config):
        if "output" in chunk:
            response = chunk["output"]
    return response

async def main(request: Request):
    sub = request.headers.get("X-Beamlit-Sub", str(uuid.uuid4()))
    config = {"configurable": {"thread_id": sub}}
    response = ""
    body = await request.json()
    all_responses = []
    for chunk in agent_executor.stream(body, config):
        all_responses.append(chunk)
        if "output" in chunk:
            response = chunk["output"]
    if chain:
        response = await chain_function(all_responses, config)
    return response
