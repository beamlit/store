import logging
import uuid

from fastapi import Request, Response
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from common.bl_config import BL_CONFIG

# this is dynamically generated, so ignore linting
from .beamlit import chains, functions  # type: ignore

logger = logging.getLogger(__name__)

global model

model = None

def get_base_url():
    if "model" not in BL_CONFIG:
        raise ValueError("model not found in configuration")
    return f'{BL_CONFIG["run_url"]}/{BL_CONFIG["workspace"]}/models/{BL_CONFIG["model"]}/v1'

def get_chat_model():
    headers = {"Authorization": f"Bearer {BL_CONFIG['jwt']}", "X-Beamlit-Environment": BL_CONFIG["environment"]}
    params = {"environment": BL_CONFIG["environment"]}
    return ChatOpenAI(
        base_url=get_base_url(),
        max_tokens=100,
        default_query=params,
        default_headers=headers,
        api_key="fake_api_key",
        temperature=0
    )

async def ask_agent(body, tools, agent_config):
    global model
    if model is None:
        model = get_chat_model()
        logger.info(f"Chat model configured, using: {BL_CONFIG['model']}")

    memory = MemorySaver()
    agent = create_react_agent(model, tools, checkpointer=memory)
    all_responses = []
    for chunk in agent.stream({"messages": [("user", body["input"])]}, config=agent_config):
        # Do update asynchronously of task in control plane, use a queue to update the task
        all_responses.append(chunk)
    return all_responses

async def main(request: Request):
    """
        name: beamlit-agent
        display_name: AI Beamlit Agent
        description: A chat agent using a compatible Beamlit Model to handle your tasks.
        type: agent
        framework: langchain
        configuration:
        - name: model
            display_name: Model
            type: selectbeamlitmodel
            description: The Beamlit Model to use.
            available_models:
            - meta-llama/Llama-3.2-1B-Instruct
            required: true
    """
    sub = request.headers.get("X-Beamlit-Sub", str(uuid.uuid4()))
    agent_config = {"configurable": {"thread_id": sub}}
    body = await request.json()
    if body.get("inputs"):
        body["input"] = body["inputs"]

    responses = await ask_agent(body, chains + functions, agent_config)
    debug = request.query_params.get('debug') in ["true", "True", "TRUE"]
    if debug:
        return responses
    else:
        content = responses[-1]["agent"]["messages"][-1].content
        return Response(content=content, headers={"Content-Type": "text/plain"}, status_code=200)


if __name__ == "__main__":
    main()
