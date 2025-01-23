import uuid

from beamlit.agents import agent
from beamlit.api.agents import get_agent
from beamlit.authentication import new_client
from beamlit.common.settings import get_settings
from fastapi import Request

settings = get_settings()
client = new_client()
bl_agent = get_agent.sync_detailed(
    agent_name=settings.name,
    environment=settings.environment,
    client=client,
).parsed

@agent(
    agent={
        "metadata": {
            "name": bl_agent.metadata.name,
            "environment": bl_agent.metadata.environment,
        },
        "spec": {
            "description": bl_agent.spec.description,
            "model": bl_agent.spec.model,
            "agent_chain": bl_agent.spec.agent_chain,
        },
    },
    remote_functions=bl_agent.spec.functions,
)
async def main(request: Request, agent):
    body = await request.json()
    agent_config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    if body.get("inputs"):
        body["input"] = body["inputs"]
    agent_body = {"messages": [("user", body["input"])]}
    responses = []

    async for chunk in agent.astream(agent_body, config=agent_config):
        responses.append(chunk)
    content = responses[-1]
    return content["agent"]["messages"][-1].content
