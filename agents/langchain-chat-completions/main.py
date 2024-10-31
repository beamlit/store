import uuid
from typing import Any

from fastapi import Request
from langchain import hub
from langchain.agents import AgentExecutor, create_json_chat_agent
from langchain_openai import ChatOpenAI

from .beamlit import BeamlitBurgerOrder, tools

chain = True
# Create the agent
prompt = hub.pull("hwchase17/react-chat-json")
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
agent = create_json_chat_agent(model, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)

async def main(request: Request):
    sub = request.headers.get("X-Beamlit-Sub", str(uuid.uuid4()))
    config = {"configurable": {"thread_id": sub}}
    response = ""
    body = await request.json()
    for chunk in agent_executor.stream(body, config):
        print(chunk["messages"])
        if "output" in chunk:
            response = chunk["output"]
    if chain:
        tools_two = [BeamlitBurgerOrder()]
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        agent_two = create_json_chat_agent(llm, tools_two, prompt)
        agent_two_executor = AgentExecutor(agent=agent_two, tools=tools_two)
        for chunk in agent_two_executor.stream({"input": body["input"] + "\n" + response}, config):
            print(chunk["messages"])
            if "output" in chunk:
                response = chunk["output"]
    return response
